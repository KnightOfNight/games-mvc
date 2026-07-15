"""v20 brief 4 (#1/#2/#31): UI layout server surface.

Covers the state-sync payload's location names+colors and combat-membership
boolean, the fight-info enemy rows, and the ping/pong echo for the
connection indicator.
"""
import asyncio

from django.contrib.auth.models import User
from django.test import TestCase

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    Archetype, Area, Character, CombatSession, NpcDefinition, NpcInstance,
    Origin, Room, Zone,
)


def make_world(prefix):
    zone = Zone.objects.create(
        name=f'{prefix} Zone',
        slug=f'{prefix}-zone',
        genre_tone='Test',
        danger_level='beginner',
        description='A test zone.',
        theme_color='#B387E8',
    )
    area = Area.objects.create(
        zone=zone, name=f'{prefix} Area', slug=f'{prefix}-area',
        theme_color='#C9A0DC',
    )
    room_with_area = Room.objects.create(
        zone=zone, area=area, name=f'{prefix} Areaful',
        description='Long.', brief_description='Brief.',
        coord_x=0, coord_y=0,
    )
    room_without_area = Room.objects.create(
        zone=zone, name=f'{prefix} Arealess',
        description='Long.', brief_description='Brief.',
        coord_x=0, coord_y=1,
    )
    return zone, area, room_with_area, room_without_area


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


def make_npc(prefix, room, name='cave spider', hp=12, hp_max=20):
    definition, _ = NpcDefinition.objects.get_or_create(
        name=name, slug=f'{prefix}-{name.replace(" ", "-")}',
        defaults=dict(
            description='A test enemy.', genre_tag='fantasy',
            base_vitality=hp_max, base_str=1, base_dex=1, base_end=1,
            base_int=1, base_wis=1, base_per=1,
        ),
    )
    return NpcInstance.objects.create(
        definition=definition, current_room=room, spawn_room=room,
        vitality_current=hp, vitality_max=hp_max,
    )


# Raw sync functions behind the database_sync_to_async wrappers, callable
# on this thread from plain TestCase tests.
_status_payload = SkylandConsumer.__dict__['_status_payload'].func
_fight_enemies = SkylandConsumer.__dict__['_fight_enemies'].func


class StatusPayloadTests(TestCase):
    """#1: server-delivered location names+colors; #2: in_combat boolean."""

    def setUp(self):
        self.zone, self.area, self.room, self.bare_room = make_world('sp')
        self.char = make_character('sp', self.room)
        self.consumer = SkylandConsumer()

    def test_location_fields_with_area(self):
        payload = _status_payload(self.consumer, self.char, self.room)
        self.assertEqual(payload['zone_name'], 'sp Zone')
        self.assertEqual(payload['zone_color'], '#B387E8')
        self.assertEqual(payload['area_name'], 'sp Area')
        self.assertEqual(payload['area_color'], '#C9A0DC')
        self.assertEqual(payload['room_name'], 'sp Areaful')

    def test_location_fields_without_area(self):
        payload = _status_payload(self.consumer, self.char, self.bare_room)
        self.assertEqual(payload['zone_name'], 'sp Zone')
        self.assertIsNone(payload['area_name'])
        self.assertIsNone(payload['area_color'])
        self.assertEqual(payload['room_name'], 'sp Arealess')

    def test_in_combat_boolean_tracks_session_membership(self):
        payload = _status_payload(self.consumer, self.char, self.room)
        self.assertIs(payload['in_combat'], False)

        session = CombatSession.objects.create(room=self.room)
        session.characters.add(self.char)
        payload = _status_payload(self.consumer, self.char, self.room)
        self.assertIs(payload['in_combat'], True)

        session.is_active = False
        session.save(update_fields=['is_active'])
        payload = _status_payload(self.consumer, self.char, self.room)
        self.assertIs(payload['in_combat'], False)


class FightEnemiesTests(TestCase):
    """#2: fight-info rows — every session NPC, hp, and the focus flag."""

    def setUp(self):
        self.zone, self.area, self.room, _ = make_world('fe')
        self.char = make_character('fe', self.room)
        self.consumer = SkylandConsumer()
        self.session = CombatSession.objects.create(room=self.room)
        self.session.characters.add(self.char)
        self.npc_a = make_npc('fe-a', self.room, hp=12, hp_max=20)
        self.npc_b = make_npc('fe-b', self.room, hp=5, hp_max=20)
        self.session.npcs.add(self.npc_a, self.npc_b)

    def test_rows_carry_hp_and_focus(self):
        self.session.focus_npc = self.npc_b
        self.session.save(update_fields=['focus_npc'])
        rows = _fight_enemies(self.consumer, self.session)
        self.assertEqual(len(rows), 2)
        by_hp = {r['hp']: r for r in rows}
        self.assertEqual(by_hp[12]['hp_max'], 20)
        self.assertIs(by_hp[12]['focused'], False)
        self.assertIs(by_hp[5]['focused'], True)
        # Same-name NPCs render positionally, as combat messages do today.
        names = sorted(r['name'] for r in rows)
        self.assertEqual(names, ['the first cave spider', 'the second cave spider'])

    def test_focus_falls_back_to_first_when_unset(self):
        rows = _fight_enemies(self.consumer, self.session)
        self.assertEqual([r['focused'] for r in rows], [True, False])

    def test_dead_npcs_are_excluded(self):
        self.npc_a.is_alive = False
        self.npc_a.save(update_fields=['is_alive'])
        rows = _fight_enemies(self.consumer, self.session)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['hp'], 5)


class PingPongTests(TestCase):
    """#31: ping is echoed as pong with the same nonce; nothing else is
    trusted or reflected."""

    def _consumer(self, sent):
        consumer = SkylandConsumer()
        consumer._character_is_dying = False

        async def fake_send_json(content, close=False):
            sent.append(content)

        consumer.send_json = fake_send_json
        return consumer

    def test_ping_echoes_nonce(self):
        sent = []
        consumer = self._consumer(sent)
        asyncio.run(consumer.receive_json({'type': 'ping', 'nonce': 42}))
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['type'], 'pong')
        self.assertEqual(sent[0]['nonce'], 42)
        self.assertIn('ts', sent[0])

    def test_malformed_nonce_is_dropped_not_reflected(self):
        for bad in ('42', None, True, 1.5, {'n': 1}):
            sent = []
            consumer = self._consumer(sent)
            asyncio.run(consumer.receive_json({'type': 'ping', 'nonce': bad}))
            self.assertEqual(sent, [], f'nonce {bad!r} should be dropped')

    def test_ping_works_while_dying(self):
        sent = []
        consumer = self._consumer(sent)
        consumer._character_is_dying = True
        asyncio.run(consumer.receive_json({'type': 'ping', 'nonce': 7}))
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['type'], 'pong')
