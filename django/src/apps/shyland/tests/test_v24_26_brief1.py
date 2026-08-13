"""V24.26 Brief 1 (#38 attunement, #30 shard relay; GDD §2.11).

Coverage per the brief's Step 8: the Character.attuned_node model
surface (recall_room gone), attune's three exhaustive cases and its
gating (dying deny-by-default; no combat gate — structurally safe),
the shard relay's sphere-only destination pool (listing, completion,
and direct-attempt refusal — the operator callout on #30), relay
travel end to end, home's completion-time bond resolution, the death
respawn following the bond, the stats sheet's Home: row, and the
chart/help sync.
"""

from asgiref.sync import sync_to_async
from django.core.exceptions import FieldDoesNotExist
from django.db import models as dj_models
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import (
    ATTUNE_ALREADY_LINES, ATTUNE_NO_NODE_LINES, ATTUNE_SUCCESS_LINES,
    SkylandConsumer,
)
from apps.shyland.models import (
    Character, Room, RoomVisit, TravelMessage, TravelNode,
    resolve_home_node, resolve_home_room,
)
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)
from apps.shyland.tests.test_new_commands import quiet_home_consumer
from apps.shyland.tests.test_zone_locks import warn_texts


def make_room(zone, name, x, y):
    return Room.objects.create(
        zone=zone, name=name,
        description=f'The long form of {name}.',
        brief_description=f'{name}, briefly.',
        coord_x=x, coord_y=y,
    )


def make_network_world(prefix):
    """One zone: the Heart (founding obelisk), a second sphere, two
    shards, and a nodeless wild room."""
    zone, wild = make_world(prefix)
    heart_room = make_room(zone, f'{prefix} Heart', 5, 5)
    sphere_room = make_room(zone, f'{prefix} Crownroom', 6, 5)
    shard_room = make_room(zone, f'{prefix} Fordroom', 7, 5)
    shard2_room = make_room(zone, f'{prefix} Cragroom', 8, 5)
    heart = TravelNode.objects.create(
        room=heart_room, travel_name='The Convergence', node_type='obelisk',
        listing_description='The founding obelisk.')
    sphere = TravelNode.objects.create(
        room=sphere_room, travel_name=f'{prefix} Crown', node_type='obelisk',
        listing_description='A far sphere.')
    shard = TravelNode.objects.create(
        room=shard_room, travel_name=f'{prefix} Fordwatch',
        node_type='checkpoint', listing_description='A river shard.')
    shard2 = TravelNode.objects.create(
        room=shard2_room, travel_name=f'{prefix} Cragfoot',
        node_type='checkpoint', listing_description='A mountain shard.')
    return zone, wild, heart, sphere, shard, shard2


def reveal(character, *nodes):
    for node in nodes:
        RoomVisit.objects.create(character=character, room=node.room)


def stand_at(character, room):
    Character.objects.filter(pk=character.pk).update(current_room=room)
    character.current_room = room
    character.current_room_id = room.pk


def report_text(sent):
    """Flatten every report message's lines to one searchable string
    (k/v/segs and table-cell forms alike)."""
    chunks = []
    for m in sent:
        for entry in m.get('lines', []):
            if 'segs' in entry:
                chunks.append(''.join(
                    seg['t'] if isinstance(seg, dict) else str(seg)
                    for seg in entry['segs']))
            else:
                k = entry.get('k', '') or ''
                v = entry.get('v', '') or ''
                if isinstance(v, list):
                    v = ' '.join(
                        ''.join(s[0] if isinstance(s, tuple) else str(s)
                                for s in (cell if isinstance(cell, list)
                                          else [cell]))
                        for cell in v)
                chunks.append(f'{k}{v}')
    return '\n'.join(chunks)


class AttunedNodeModelTests(TestCase):
    """Brief Step 8.1: the model surface."""

    def test_attuned_node_present_nullable_set_null(self):
        field = Character._meta.get_field('attuned_node')
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertIs(field.remote_field.on_delete, dj_models.SET_NULL)
        self.assertIs(field.remote_field.model, TravelNode)
        self.assertEqual(field.remote_field.related_name,
                         'attuned_characters')

    def test_recall_room_absent(self):
        with self.assertRaises(FieldDoesNotExist):
            Character._meta.get_field('recall_room')

    def test_resolver_null_is_founding_node(self):
        zone, wild, heart, sphere, shard, shard2 = make_network_world('rmn')
        char = make_character('rmn', wild)
        self.assertEqual(resolve_home_node(char).pk, heart.pk)
        self.assertEqual(resolve_home_room(char).pk, heart.room.pk)

    def test_resolver_follows_the_bond(self):
        zone, wild, heart, sphere, shard, shard2 = make_network_world('rmb')
        char = make_character('rmb', wild)
        Character.objects.filter(pk=char.pk).update(attuned_node=shard)
        char.refresh_from_db()
        self.assertEqual(resolve_home_node(char).pk, shard.pk)
        self.assertEqual(resolve_home_room(char).pk, shard.room.pk)


class AttuneCommandTests(TransactionTestCase):
    """Brief Step 8.2: the three exhaustive cases."""

    async def test_no_node_room_warns_from_pool(self):
        zone, wild, *_ = await sync_to_async(make_network_world)('atA')
        char = await sync_to_async(make_character)('atA', wild)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_attune()
        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        self.assertIn(warns[0], ATTUNE_NO_NODE_LINES)
        await sync_to_async(char.refresh_from_db)()
        self.assertIsNone(char.attuned_node_id)

    async def test_bondless_at_heart_is_already_attuned(self):
        def setup():
            zone, wild, heart, *_ = make_network_world('atB')
            char = make_character('atB', wild)
            stand_at(char, heart.room)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_attune()
        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        self.assertIn(warns[0], ATTUNE_ALREADY_LINES)
        await sync_to_async(char.refresh_from_db)()
        self.assertIsNone(char.attuned_node_id)

    async def test_explicit_bond_already_attuned(self):
        def setup():
            zone, wild, heart, sphere, shard, shard2 = (
                make_network_world('atC'))
            char = make_character('atC', wild)
            Character.objects.filter(pk=char.pk).update(attuned_node=shard)
            char.refresh_from_db()
            _ = char.user  # re-warm the FK cache refresh_from_db cleared
            stand_at(char, shard.room)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_attune()
        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        self.assertIn(warns[0], ATTUNE_ALREADY_LINES)

    async def test_new_node_moves_the_bond_with_ceremony(self):
        def setup():
            zone, wild, heart, sphere, shard, shard2 = (
                make_network_world('atD'))
            char = make_character('atD', wild)
            stand_at(char, shard.room)
            return char, shard
        char, shard = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_attune()
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.attuned_node_id, shard.pk)
        msgs = [m for m in outputs(sent) if m['category'] == 'success']
        self.assertEqual(len(msgs), 1)
        # The pooled ceremony ends in the stable, exact parenthetical.
        expected = [f'{line} (Home: {shard.travel_name})'
                    for line in ATTUNE_SUCCESS_LINES]
        self.assertIn(msgs[0]['text'], expected)

    async def test_reattuning_at_heart_sets_the_founding_node(self):
        def setup():
            zone, wild, heart, sphere, shard, shard2 = (
                make_network_world('atE'))
            char = make_character('atE', wild)
            Character.objects.filter(pk=char.pk).update(attuned_node=shard)
            char.refresh_from_db()
            _ = char.user  # re-warm the FK cache refresh_from_db cleared
            stand_at(char, heart.room)
            return char, heart
        char, heart = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_attune()
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.attuned_node_id, heart.pk)
        msgs = [m for m in outputs(sent) if m['category'] == 'success']
        expected = [f'{line} (Home: The Convergence)'
                    for line in ATTUNE_SUCCESS_LINES]
        self.assertIn(msgs[0]['text'], expected)


class AttuneGatingTests(TransactionTestCase):
    """Brief Step 8.3: dying refuses (deny-by-default); no combat gate."""

    async def test_refused_while_dying(self):
        zone, wild, *_ = await sync_to_async(make_network_world)('agA')
        char = await sync_to_async(make_character)('agA', wild)
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer._character_is_dying = True
        await consumer.receive_json({'text': 'attune'})
        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        self.assertIn('You are dying!', warns[0])

    async def test_not_in_combat_blocked_set(self):
        # Design rule 8: no combat gate, structurally — every attunable
        # room is a safe room, so in combat attune can only ever draw
        # the no-node warn.
        self.assertNotIn('attune', SkylandConsumer.COMBAT_BLOCKED)
        self.assertNotIn('attune', SkylandConsumer.DYING_ALLOWED)

    async def test_in_combat_nodeless_room_draws_no_node_warn(self):
        zone, wild, *_ = await sync_to_async(make_network_world)('agB')
        char = await sync_to_async(make_character)('agB', wild)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('attune', '')
        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        self.assertIn(warns[0], ATTUNE_NO_NODE_LINES)


class RelayPoolTests(TransactionTestCase):
    """Brief Step 8.4 (the #30 callout): a shard offers exactly the
    revealed spheres — unrevealed spheres absent, shards never."""

    def _world(self, prefix):
        zone, wild, heart, sphere, shard, shard2 = (
            make_network_world(prefix))
        char = make_character(prefix, wild)
        # Revealed: the Heart, both shards. NOT the second sphere.
        reveal(char, heart, shard, shard2)
        stand_at(char, shard.room)
        return char, heart, sphere, shard, shard2

    async def test_shard_listing_offers_revealed_spheres_only(self):
        char, heart, sphere, shard, shard2 = (
            await sync_to_async(self._world)('rpA'))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel('')
        text = report_text(sent)
        self.assertIn('The Convergence', text)
        self.assertNotIn(sphere.travel_name, text)   # unrevealed sphere
        self.assertNotIn(shard2.travel_name, text)   # revealed shard
        self.assertIn('Shard', text)                 # the opener's voice

    async def test_shard_completion_completes_spheres_only(self):
        char, heart, sphere, shard, shard2 = (
            await sync_to_async(self._world)('rpB'))
        consumer = make_stub_consumer(char, [])
        options = await consumer._complete_travel('')
        self.assertEqual(options, ['the convergence'])

    async def test_shard_direct_attempt_at_unrevealed_sphere_refused(self):
        char, heart, sphere, shard, shard2 = (
            await sync_to_async(self._world)('rpC'))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel(sphere.travel_name.lower())
        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        self.assertIn('knows no such place', warns[0])
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, shard.room.pk)

    async def test_shard_direct_attempt_at_revealed_shard_refused(self):
        char, heart, sphere, shard, shard2 = (
            await sync_to_async(self._world)('rpD'))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel(shard2.travel_name.lower())
        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        self.assertIn('knows no such place', warns[0])
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, shard.room.pk)

    async def test_obelisk_pool_unchanged_full_revealed_set(self):
        char, heart, sphere, shard, shard2 = (
            await sync_to_async(self._world)('rpE'))
        await sync_to_async(stand_at)(char, heart.room)
        consumer = make_stub_consumer(char, [])
        options = await consumer._complete_travel('')
        self.assertEqual(
            options,
            sorted([shard.travel_name.lower(), shard2.travel_name.lower()]))


class RelayTravelTests(TransactionTestCase):
    """Brief Step 8.5: relay travel end to end, standard messaging."""

    async def test_shard_relays_to_the_heart(self):
        def setup():
            zone, wild, heart, sphere, shard, shard2 = (
                make_network_world('rt'))
            char = make_character('rt', wild)
            reveal(char, heart, shard)
            stand_at(char, shard.room)
            TravelMessage.objects.create(
                category='traveler', text='The stone takes you.')
            TravelMessage.objects.create(
                category='departure', text='{name} is swept away.')
            TravelMessage.objects.create(
                category='arrival', text='{name} arrives in a shimmer.')
            return char, heart
        char, heart = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel('the convergence')
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, heart.room.pk)
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('The stone takes you.', texts)
        broadcast = [e for g, e in consumer.channel_layer.events]
        broadcast_texts = [e.get('text', '') for e in broadcast]
        self.assertIn('rt Char is swept away.', broadcast_texts)
        self.assertIn('rt Char arrives in a shimmer.', broadcast_texts)


class HomeBondTests(TransactionTestCase):
    """Brief Step 8.6: home delivers to the bond, resolved at landing."""

    def _world(self, prefix):
        zone, wild, heart, sphere, shard, shard2 = (
            make_network_world(prefix))
        char = make_character(prefix, wild)
        return char, wild, heart, shard

    async def test_null_bond_delivers_to_the_heart(self):
        char, wild, heart, shard = await sync_to_async(self._world)('hbA')
        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        await consumer.delayed_actions['home']
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, heart.room.pk)

    async def test_bond_delivers_to_the_attuned_room(self):
        char, wild, heart, shard = await sync_to_async(self._world)('hbB')
        await sync_to_async(
            Character.objects.filter(pk=char.pk).update)(attuned_node=shard)
        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        await consumer.delayed_actions['home']
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, shard.room.pk)

    async def test_already_at_bonded_home_kindly_refused(self):
        char, wild, heart, shard = await sync_to_async(self._world)('hbC')

        def bond_and_stand():
            Character.objects.filter(pk=char.pk).update(attuned_node=shard)
            stand_at(char, shard.room)
        await sync_to_async(bond_and_stand)()
        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        self.assertEqual(outputs(sent)[0]['text'], 'You are already home.')
        self.assertEqual(outputs(sent)[0]['category'], 'warn')

    async def test_bond_changed_mid_countdown_lands_at_new_home(self):
        # Design rule 7: the destination resolves when the fog parts,
        # not when the countdown starts.
        char, wild, heart, shard = await sync_to_async(self._world)('hbD')
        sent = []
        consumer = quiet_home_consumer(char, sent)
        consumer.HOME_CADENCE = (0.5, 0, 0)
        await consumer.cmd_home()          # initiated with a null bond
        await sync_to_async(
            Character.objects.filter(pk=char.pk).update)(attuned_node=shard)
        await consumer.delayed_actions['home']
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, shard.room.pk)


class RespawnBondTests(TransactionTestCase):
    """Brief Step 8.7: death respawn follows the bond (engine harness;
    the visit-recording intent lives in test_room_visits'
    test_respawn_records_visit_at_home_room)."""

    def _engine(self):
        from apps.shyland.management.commands.run_tick_engine import Command
        cmd = Command()
        cmd.player_sends = []

        async def record_send(character_pk, text, category, status,
                              event=None, fight=None):
            cmd.player_sends.append((character_pk, text, category, status))

        async def record_broadcast(room_id, text, category='room',
                                   exclude_pk=None, exclude_pks=None):
            pass

        async def all_online(pks):
            return set(pks)
        cmd.send_to_player = record_send
        cmd.broadcast_to_room = record_broadcast
        cmd._online_character_pks = all_online
        return cmd

    def _dying_world(self, prefix, bonded):
        zone, wild, heart, sphere, shard, shard2 = (
            make_network_world(prefix))
        char = make_character(prefix, wild)
        updates = {
            'is_dying': True,
            'dying_since': timezone.now() - timezone.timedelta(seconds=120),
            'vitality_current': 0,
            'longevity_current': 10,
        }
        if bonded:
            updates['attuned_node'] = shard
        Character.objects.filter(pk=char.pk).update(**updates)
        char.refresh_from_db()
        return char, heart, shard

    async def test_respawn_at_the_bonded_node_full_bars(self):
        char, heart, shard = await sync_to_async(
            self._dying_world)('rsA', bonded=True)
        cmd = self._engine()
        await cmd.process_combat(1)
        await sync_to_async(char.refresh_from_db)()
        self.assertFalse(char.is_dying)
        self.assertEqual(char.current_room_id, shard.room.pk)
        self.assertEqual(char.vitality_current, char.vitality_max)
        self.assertEqual(char.longevity_current, char.longevity_max)
        respawn_texts = [t for pk, t, c, s in cmd.player_sends
                         if pk == char.pk and 'awakened' in t]
        self.assertEqual(len(respawn_texts), 1)
        self.assertIn(shard.room.name, respawn_texts[0])

    async def test_respawn_null_bond_at_the_heart(self):
        char, heart, shard = await sync_to_async(
            self._dying_world)('rsB', bonded=False)
        cmd = self._engine()
        await cmd.process_combat(1)
        await sync_to_async(char.refresh_from_db)()
        self.assertFalse(char.is_dying)
        self.assertEqual(char.current_room_id, heart.room.pk)


class ChartAndStatsTests(TransactionTestCase):
    """Brief Steps 8.8/8b: help lists attune; the stats Home: row sits
    directly under the Player line."""

    async def test_help_lists_attune(self):
        zone, wild, *_ = await sync_to_async(make_network_world)('csA')
        char = await sync_to_async(make_character)('csA', wild)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_help()
        text = report_text(sent)
        self.assertIn('attune', text)

    def test_attune_in_dispatch_table_bare_verb(self):
        handler, takes_args = SkylandConsumer.COMMAND_TABLE['attune']
        self.assertEqual(handler, 'cmd_attune')
        self.assertFalse(takes_args)

    async def test_stats_home_row_bondless_and_bonded(self):
        def setup():
            zone, wild, heart, sphere, shard, shard2 = (
                make_network_world('csB'))
            char = make_character('csB', wild)
            return char, shard
        char, shard = await sync_to_async(setup)()

        async def stats_lines(c):
            sent = []
            consumer = make_stub_consumer(c, sent)
            await consumer.cmd_stats()
            report = next(m for m in sent if 'lines' in m)
            return [(e.get('k', '') or '') + (e.get('v', '') or '')
                    for e in report['lines']]

        lines = await stats_lines(char)
        self.assertTrue(lines[1].startswith('  Player:'))
        self.assertEqual(lines[2], '  Home: The Convergence')

        await sync_to_async(
            Character.objects.filter(pk=char.pk).update)(attuned_node=shard)
        lines = await stats_lines(char)
        self.assertTrue(lines[1].startswith('  Player:'))
        self.assertEqual(lines[2], f'  Home: {shard.travel_name}')
