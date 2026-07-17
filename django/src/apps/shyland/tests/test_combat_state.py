"""v21 brief 3 (#52/#64/#17): combat state fixes.

Covers the heal lost-update race (atomic bar mutations), the canonical
(spawned_at, pk) NPC order across listing/resolver/index/ordinals, and
respawned aggressive NPCs engaging present players on the spawn tick.
"""
import asyncio

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from apps.shyland.combat_utils import npc_display_name
from apps.shyland.command_grammar import resolve
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.effect_utils import apply_effect_definition
from apps.shyland.models import (
    Archetype, Character, CombatSession, EffectComponent, EffectDefinition,
    NpcDefinition, NpcInstance, Origin, Room, RoomSpawn, Zone,
)


def make_world(prefix):
    zone = Zone.objects.create(
        name=f'{prefix} Zone', slug=f'{prefix}-zone',
        genre_tone='Test', danger_level='beginner',
        description='A test zone.',
    )
    room = Room.objects.create(
        zone=zone, name=f'{prefix} Room',
        description='Long.', brief_description='Brief.',
        coord_x=0, coord_y=0,
    )
    return zone, room


def make_character(prefix, room):
    user = User.objects.create_user(username=f'{prefix}_user', password='x')
    origin = Origin.objects.create(
        name=f'{prefix} Origin', slug=f'{prefix}-origin',
        acuity_baseline=1.0, acuity_band_low=0.8, acuity_band_high=1.2,
    )
    archetype = Archetype.objects.create(
        name=f'{prefix} Archetype', slug=f'{prefix}-archetype',
        primary_stat_1='str', primary_stat_2='dex',
    )
    return Character.objects.create(
        user=user, name=f'{prefix} Char',
        origin=origin, archetype=archetype,
        current_room=room, recall_room=room,
    )


def make_npc_definition(prefix, name='cave spider', aggressive=False):
    return NpcDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.replace(" ", "-")}',
        description='A test enemy.', genre_tag='fantasy',
        indefinite_article='a',
        is_aggressive=aggressive,
        base_vitality=20, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )


def make_npc(definition, room, hp=20):
    return NpcInstance.objects.create(
        definition=definition, current_room=room, spawn_room=room,
        vitality_current=hp, vitality_max=hp,
    )


def make_heal_definition(prefix, magnitude=25.0, component='restore_vitality'):
    definition = EffectDefinition.objects.create(
        name=f'{prefix} Heal', slug=f'{prefix}-heal',
    )
    EffectComponent.objects.create(
        definition=definition, component_type=component,
        magnitude_base=magnitude, magnitude_scaling=0.0,
        duration_base=0.0, duration_scaling=0.0,
    )
    return definition


class HealLostUpdateTests(TestCase):
    """#52: consumer heals are atomic — tick-engine damage persisted after
    the consumer's last refresh is never resurrected."""

    def setUp(self):
        self.zone, self.room = make_world('hl')
        self.char = make_character('hl', self.room)
        Character.objects.filter(pk=self.char.pk).update(
            vitality_current=100, vitality_max=100,
            longevity_current=100, longevity_max=100,
        )

    def test_stale_heal_does_not_resurrect_persisted_damage(self):
        # The consumer's cached character still believes vitality is 100...
        stale = Character.objects.get(pk=self.char.pk)
        self.assertEqual(stale.vitality_current, 100)
        # ...while the tick engine has persisted damage since.
        Character.objects.filter(pk=self.char.pk).update(vitality_current=40)

        msgs = apply_effect_definition(
            make_heal_definition('hl'), stale, mk_tier=1)

        self.char.refresh_from_db()
        # Old code: min(stale 100 + 25, 100) = 100 — damage resurrected.
        # Atomic: persisted 40 + 25 = 65.
        self.assertEqual(self.char.vitality_current, 65)
        self.assertIn('+25 Vitality', msgs[0])

    def test_heal_still_clamps_to_max(self):
        stale = Character.objects.get(pk=self.char.pk)
        Character.objects.filter(pk=self.char.pk).update(vitality_current=90)
        apply_effect_definition(make_heal_definition('hl2'), stale, mk_tier=1)
        self.char.refresh_from_db()
        self.assertEqual(self.char.vitality_current, 100)

    def test_longevity_restore_is_atomic(self):
        stale = Character.objects.get(pk=self.char.pk)
        Character.objects.filter(pk=self.char.pk).update(longevity_current=30)
        apply_effect_definition(
            make_heal_definition('hl3', component='restore_longevity'),
            stale, mk_tier=1)
        self.char.refresh_from_db()
        self.assertEqual(self.char.longevity_current, 55)

    def test_acuity_restore_applies_to_persisted_value(self):
        # Baseline 1.0. Engine drift has persisted 0.4; the cached object
        # still believes 1.0 (at baseline — old code would be a no-op).
        stale = Character.objects.get(pk=self.char.pk)
        Character.objects.filter(pk=self.char.pk).update(acuity_current=0.4)
        msgs = apply_effect_definition(
            make_heal_definition('hl4', magnitude=0.3,
                                 component='restore_acuity'),
            stale, mk_tier=1)
        self.char.refresh_from_db()
        self.assertAlmostEqual(self.char.acuity_current, 0.7, places=3)
        self.assertIn('0.7', msgs[0])

    def test_acuity_restore_never_overshoots_baseline(self):
        stale = Character.objects.get(pk=self.char.pk)
        Character.objects.filter(pk=self.char.pk).update(acuity_current=0.9)
        apply_effect_definition(
            make_heal_definition('hl5', magnitude=0.3,
                                 component='restore_acuity'),
            stale, mk_tier=1)
        self.char.refresh_from_db()
        self.assertAlmostEqual(self.char.acuity_current, 1.0, places=3)


_get_live_npcs_in_room = SkylandConsumer.__dict__['get_live_npcs_in_room'].func


class NpcOrderingTests(TestCase):
    """#64: one authoritative NPC order — listing, resolver default pick,
    N.noun index, and message ordinals all agree on (spawned_at, pk)."""

    def setUp(self):
        self.zone, self.room = make_world('no')
        self.definition = make_npc_definition('no')
        self.first = make_npc(self.definition, self.room)
        self.second = make_npc(self.definition, self.room)
        self.consumer = SkylandConsumer()

    def listing(self):
        return _get_live_npcs_in_room(self.consumer, self.room)

    def test_listing_is_spawn_ordered(self):
        self.assertEqual([n.pk for n in self.listing()],
                         [self.first.pk, self.second.pk])

    def test_resolver_default_pick_is_the_first(self):
        res = resolve('attack', 'cave spider', self.listing())
        self.assertTrue(res.ok)
        self.assertEqual(res.items[0].pk, self.first.pk)

    def test_index_form_picks_the_second(self):
        res = resolve('attack', '2.cave spider', self.listing())
        self.assertTrue(res.ok)
        self.assertEqual(res.items[0].pk, self.second.pk)

    def test_message_ordinals_agree_with_listing(self):
        npcs = self.listing()
        self.assertEqual(npc_display_name(npcs[0], npcs),
                         'the first cave spider')
        self.assertEqual(npc_display_name(npcs[1], npcs),
                         'the second cave spider')

    def test_solo_npc_renders_no_ordinal(self):
        self.second.delete()
        npcs = self.listing()
        self.assertEqual(npc_display_name(npcs[0], npcs), 'the cave spider')


class RespawnAggroTests(TransactionTestCase):
    """#17: an aggressive NPC (re)spawning into an occupied room engages on
    the spawn tick — no player movement required. Empty rooms and passive
    NPCs engage nothing."""

    def _command(self):
        from apps.shyland.management.commands.run_tick_engine import Command
        cmd = Command()
        cmd.broadcasts = []
        cmd.player_sends = []

        async def record_broadcast(room_id, text, category='room',
                                   exclude_pk=None, exclude_pks=None):
            cmd.broadcasts.append((room_id, text, category, exclude_pks))

        async def record_send(character_pk, text, category, status,
                              event=None, fight=None):
            cmd.player_sends.append((character_pk, status, fight))

        async def all_online(pks):
            return set(pks)

        cmd.broadcast_to_room = record_broadcast
        cmd.send_to_player = record_send
        cmd._online_character_pks = all_online
        return cmd

    def _spawn(self, definition, room):
        return RoomSpawn.objects.create(
            room=room, npc_definition=definition, mk_tier=1,
            count=1, is_active=True,
        )

    def test_respawned_aggro_engages_present_player_on_spawn_tick(self):
        zone, room = make_world('ra')
        char = make_character('ra', room)
        definition = make_npc_definition('ra', aggressive=True)
        self._spawn(definition, room)

        cmd = self._command()
        asyncio.run(cmd.process_npc_respawn())

        npc = NpcInstance.objects.get(definition=definition)
        session = CombatSession.objects.filter(
            is_active=True, characters=char).first()
        self.assertIsNotNone(session)
        self.assertIn(npc.pk, [n.pk for n in session.npcs.all()])

        combat_lines = [b for b in cmd.broadcasts if b[2] == 'combat']
        self.assertEqual(len(combat_lines), 1)
        # No respawn message precedes, so the engagement line introduces
        # (indefinite article — the #79 first-presentation context).
        self.assertEqual(combat_lines[0][1],
                         'A cave spider snarls and moves to attack!')

        self.assertEqual(len(cmd.player_sends), 1)
        pk, status, fight = cmd.player_sends[0]
        self.assertEqual(pk, char.pk)
        self.assertTrue(fight['active'])
        self.assertTrue(status['in_combat'])

    def test_respawn_into_empty_room_engages_nothing(self):
        zone, room = make_world('re')
        other_zone, other_room = make_world('re2')
        char = make_character('re', other_room)  # elsewhere
        definition = make_npc_definition('re', aggressive=True)
        self._spawn(definition, room)

        cmd = self._command()
        asyncio.run(cmd.process_npc_respawn())

        self.assertEqual(NpcInstance.objects.filter(
            definition=definition).count(), 1)
        self.assertFalse(CombatSession.objects.filter(is_active=True).exists())
        self.assertEqual([b for b in cmd.broadcasts if b[2] == 'combat'], [])

    def test_passive_respawn_engages_nothing(self):
        zone, room = make_world('rp')
        make_character('rp', room)
        definition = make_npc_definition('rp', aggressive=False)
        self._spawn(definition, room)

        cmd = self._command()
        asyncio.run(cmd.process_npc_respawn())

        self.assertEqual(NpcInstance.objects.filter(
            definition=definition).count(), 1)
        self.assertFalse(CombatSession.objects.filter(is_active=True).exists())
