"""v25.5 brief 1 (#281/#273): the agent door — protocol 2 frame
contract, the six query kinds, the six action kinds, the kill-switch
extension over query/action frames, MC capture of door activity, the
sudo category/color pins, and the bot-name reservation (GDD §10.11).

Socket tests drive the real MCEgressConsumer with the stream/presence
client faked at ``mc._get_client`` (the test_mc_egress.py shape,
extended with the presence + xadd surface) and the channel layer
recorded at ``mc_door.get_channel_layer``. The ``moved`` consumer
branch is covered end-to-end over a real SkylandConsumer socket (the
test_room_visits.py respawn shape — requires the in-container
environment)."""

import json
import re
from pathlib import Path

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from unittest import mock

from apps.shyland import consumers as consumers_module
from apps.shyland import mc, mc_door
from apps.shyland.consumers import DIRECTIONS, SkylandConsumer
from apps.shyland.forms import CharacterCreationForm
from apps.shyland.item_utils import carry_capacity
from apps.shyland.mc_consumer import MC_PROTOCOL, MCEgressConsumer
from apps.shyland.models import (
    RESERVED_BOT_NAMES, Archetype, Character, CombatSession,
    EffectComponent, EffectComponentInstance, EffectDefinition,
    EffectInstance, ItemDefinition, ItemInstance, NpcDefinition, Origin,
    RoomVisit,
)
from apps.shyland.tests.test_mc_egress import FakeEgressClient, make_agent
from apps.shyland.tests.test_mc_kill_switch import engage_switch
from apps.shyland.tests.test_new_commands import grant_admin
from apps.shyland.tests.test_room_visits import make_character, make_world


class FakeDoorClient(FakeEgressClient):
    """The egress fake grown to the door's surface: presence keys
    (exists/keys/mget) and the emit sink (xadd)."""

    def __init__(self, window=()):
        super().__init__(window)
        self.presence = {}
        self.emitted = []

    def set_online(self, char):
        self.presence[f'shyland:online:{char.pk}'] = json.dumps(
            {'name': char.name, 'token': 'test'}).encode()

    async def exists(self, key):
        return 1 if key in self.presence else 0

    async def keys(self, pattern):
        return [k.encode() for k in self.presence]

    async def mget(self, *keys):
        return [self.presence.get(k.decode() if isinstance(k, bytes) else k)
                for k in keys]

    async def xadd(self, key, record, maxlen=None, approximate=None):
        self.emitted.append(record)


class RecordingLayer:
    """Captures the door's audited group sends."""

    def __init__(self):
        self.sent = []

    async def group_send(self, group, event):
        self.sent.append((group, event))


class DoorCommunicator:
    """Context helper: the consumer over the faked stream/presence
    client and a recording channel layer."""

    def __init__(self, user, fake, layer):
        self.user = user
        self.fake = fake
        self.layer = layer

    async def __aenter__(self):
        self.patches = [
            mock.patch.object(mc, '_get_client', lambda: self.fake),
            mock.patch.object(mc_door, 'get_channel_layer',
                              lambda: self.layer),
        ]
        for patch in self.patches:
            patch.start()
        self.comm = WebsocketCommunicator(
            MCEgressConsumer.as_asgi(), '/ws/shyland/mc/')
        self.comm.scope['user'] = self.user
        connected, _ = await self.comm.connect()
        assert connected
        hello = await self.comm.receive_json_from(timeout=10)
        assert hello == {'type': 'hello', 'protocol': MC_PROTOCOL}
        return self.comm

    async def __aexit__(self, *exc):
        await self.comm.disconnect()
        for patch in self.patches:
            patch.stop()


async def request(comm, frame):
    await comm.send_json_to(frame)
    return await comm.receive_json_from(timeout=10)


def door_records(fake, kind):
    """Emitted records of one kind, data json-decoded."""
    return [dict(r, data=json.loads(r['data']))
            for r in fake.emitted if r['kind'] == kind]


def make_equippable(prefix, name, item_type, slots, **defn_kwargs):
    # v25.12 (#311): explicit all-worn band — preserves the retired
    # empty-table fallback these fixtures ran under.
    defn_kwargs.setdefault(
        'durability_table', [{'min': 0, 'max': 100, 'penalty': 1.0}])
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type=item_type, genre_tag='fantasy', description='Test gear.',
        valid_slots=slots, scaling_base=0.0, scaling_factor=0.0,
        base_value=1, **defn_kwargs,
    )


class DoorTestBase(TransactionTestCase):
    """Fixture plumbing shared by the socket-driven door tests."""

    def _fixture(self, prefix):
        agent = make_agent(prefix)
        zone, room_a, room_b = make_world(prefix)
        char = make_character(prefix, room_a)
        return agent, zone, room_a, room_b, char

    def door(self, agent, fake=None, layer=None):
        return DoorCommunicator(agent, fake or FakeDoorClient(),
                                layer or RecordingLayer())


# ----------------------------------------------------------------------
# Pins
# ----------------------------------------------------------------------

class DoorPinTests(SimpleTestCase):

    def test_protocol_is_2(self):
        self.assertEqual(MC_PROTOCOL, 2)

    def test_sudo_color_and_rule_present(self):
        # §5.1: the chart row is GDD-landed; the license must be
        # visible in the test layer.
        path = (Path(consumers_module.__file__).parent
                / 'templates' / 'shyland' / 'game.html')
        source = path.read_text()
        self.assertIn('--sudo-color: #E24B4A;', source)
        self.assertRegex(
            source, r'\.msg-sudo\s*\{\s*color:\s*var\(--sudo-color\);')
        # Answers are events: sudo is NOT an unstamped category.
        unstamped = re.search(r'UNSTAMPED_CATEGORIES = new Set\(\[(.*?)\]\)',
                              source).group(1)
        self.assertNotIn('sudo', unstamped)


# ----------------------------------------------------------------------
# Protocol (§4)
# ----------------------------------------------------------------------

class DoorProtocolTests(DoorTestBase):

    async def test_non_member_4403_unchanged(self):
        user = await sync_to_async(User.objects.create_user)(
            username='door_nonmember', password='x')
        comm = WebsocketCommunicator(
            MCEgressConsumer.as_asgi(), '/ws/shyland/mc/')
        comm.scope['user'] = user
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        message = await comm.receive_output(timeout=10)
        self.assertEqual(message['type'], 'websocket.close')
        self.assertEqual(message['code'], 4403)
        await comm.disconnect()

    async def test_unknown_frame_type_draws_unknown_frame(self):
        agent = await sync_to_async(make_agent)('door_uf')
        async with self.door(agent) as comm:
            error = await request(comm, {'type': 'say', 'text': 'hi'})
            self.assertEqual(error,
                             {'type': 'error', 'error': 'unknown-frame'})
            pong = await request(comm, {'type': 'ping', 'nonce': 3})
            self.assertEqual(pong, {'type': 'pong', 'nonce': 3})

    async def test_missing_or_bad_id_draws_bad_frame_id_null(self):
        agent = await sync_to_async(make_agent)('door_id')
        async with self.door(agent) as comm:
            for frame in (
                {'type': 'query', 'q': 'commands'},
                {'type': 'query', 'id': 7, 'q': 'commands'},
                {'type': 'action', 'id': 'x' * 65, 'act': 'strip'},
            ):
                result = await request(comm, frame)
                self.assertEqual(result['type'], 'result')
                self.assertIsNone(result['id'])
                self.assertFalse(result['ok'])
                self.assertEqual(result['error'], 'bad-frame')

    async def test_unknown_query_and_action_kinds(self):
        agent = await sync_to_async(make_agent)('door_uk')
        async with self.door(agent) as comm:
            result = await request(
                comm, {'type': 'query', 'id': '1', 'q': 'nope'})
            self.assertEqual(result['error'], 'unknown-query')
            result = await request(
                comm, {'type': 'action', 'id': '2', 'act': 'nope'})
            self.assertEqual(result['error'], 'unknown-action')

    async def test_killed_switch_severs_query_frame_4503(self):
        agent = await sync_to_async(make_agent)('door_kq')
        async with self.door(agent) as comm:
            await sync_to_async(engage_switch)()
            await comm.send_json_to(
                {'type': 'query', 'id': '1', 'q': 'commands'})
            message = await comm.receive_output(timeout=10)
            self.assertEqual(message['type'], 'websocket.close')
            self.assertEqual(message['code'], 4503)

    async def test_killed_switch_severs_action_frame_4503(self):
        agent = await sync_to_async(make_agent)('door_ka')
        async with self.door(agent) as comm:
            await sync_to_async(engage_switch)()
            await comm.send_json_to(
                {'type': 'action', 'id': '1', 'act': 'strip',
                 'params': {'name': 'anyone'}})
            message = await comm.receive_output(timeout=10)
            self.assertEqual(message['type'], 'websocket.close')
            self.assertEqual(message['code'], 4503)


# ----------------------------------------------------------------------
# Query kinds (§4.1)
# ----------------------------------------------------------------------

class DoorQueryTests(DoorTestBase):

    async def test_commands_equals_connect_derivation(self):
        agent = await sync_to_async(make_agent)('door_cmds')
        fake = FakeDoorClient()
        async with self.door(agent, fake) as comm:
            result = await request(
                comm, {'type': 'query', 'id': 'c1', 'q': 'commands'})
            self.assertTrue(result['ok'])
            full = set(DIRECTIONS) | set(SkylandConsumer.COMMAND_TABLE)
            admin = set(SkylandConsumer.ADMIN_VERBS)
            self.assertEqual(result['data']['verbs'], sorted(full - admin))
            self.assertEqual(result['data']['admin_verbs'], sorted(admin))
            # The split reassembles to the full vocabulary.
            self.assertEqual(
                set(result['data']['verbs'])
                | set(result['data']['admin_verbs']), full)
            # §6: one agent_query record, actor_name = the agent.
            records = door_records(fake, 'agent_query')
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['actor_name'], agent.username)
            self.assertEqual(records[0]['data'],
                             {'q': 'commands', 'params': {}, 'ok': True})

    async def test_who_online_lists_present_characters_only(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_who')
        offline = await sync_to_async(make_character)('door_who2', room_b)
        fake = FakeDoorClient()
        fake.set_online(char)
        async with self.door(agent, fake) as comm:
            result = await request(
                comm, {'type': 'query', 'id': 'w1', 'q': 'who_online'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['characters'],
                             [{'id': char.pk, 'name': char.name}])

    async def test_where_is_online_offline_and_not_found(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_where')
        fake = FakeDoorClient()
        async with self.door(agent, fake) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'w1', 'q': 'where_is',
                'params': {'name': char.name.upper()}})  # case-insensitive
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {
                'id': char.pk, 'name': char.name, 'online': False,
                'room': {'id': room_a.id, 'name': room_a.name,
                         'area': None, 'zone': zone.name}})
            fake.set_online(char)
            result = await request(comm, {
                'type': 'query', 'id': 'w2', 'q': 'where_is',
                'params': {'name': char.name}})
            self.assertTrue(result['data']['online'])
            result = await request(comm, {
                'type': 'query', 'id': 'w3', 'q': 'where_is',
                'params': {'name': 'Nobody Such'}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')

    async def test_character_payload_base_and_effective_stats(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_char')

        def equip_gear():
            defn = make_equippable('door_char', 'Test Girdle', 'armor',
                                   ['WAIST'])
            ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=1, rarity='common',
                is_equipped=True, equipped_slot='WAIST',
                rolled_primary_stats=[{'stat': 'str', 'value': 4}])
        await sync_to_async(equip_gear)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'c1', 'q': 'character',
                'params': {'name': char.name}})
            self.assertTrue(result['ok'])
            data = result['data']
            self.assertEqual(data['id'], char.pk)
            self.assertEqual(data['level'], 1)
            self.assertEqual(data['origin'], char.origin.name)
            self.assertEqual(data['archetype'], char.archetype.name)
            self.assertEqual(data['stats_base']['str'], 10)
            self.assertEqual(data['stats_effective']['str'], 14)
            self.assertEqual(data['stats_effective']['dex'], 10)
            self.assertEqual(data['vitality'], [100, 100])
            self.assertEqual(data['longevity'], [100, 100])
            self.assertEqual(data['copper'], 0)
            self.assertEqual(data['unspent_stat_points'], 0)
            self.assertFalse(data['online'])
            self.assertEqual(data['room']['zone'], zone.name)

    async def test_items_filter_fields_and_cap(self):
        agent = await sync_to_async(make_agent)('door_items')

        def build():
            make_equippable('door_items', 'Iron Testmace', 'weapon',
                            ['MAIN_HAND'], is_two_handed=True,
                            tier_material_mk_min=1, tier_material_mk_max=1)
            for n in range(51):
                make_equippable('door_items', f'Bulk Test Item {n:02d}',
                                'material', [])
        await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'i1', 'q': 'items',
                'params': {'contains': 'Iron Testmace'}})
            self.assertTrue(result['ok'])
            self.assertFalse(result['data']['truncated'])
            row = result['data']['definitions'][0]
            self.assertEqual(row['name'], 'Iron Testmace')
            self.assertEqual(row['item_type'], 'weapon')
            self.assertEqual(row['valid_slots'], ['MAIN_HAND'])
            self.assertTrue(row['is_two_handed'])
            self.assertEqual(row['tier_material_mk_min'], 1)
            self.assertEqual(row['tier_material_mk_max'], 1)
            result = await request(comm, {
                'type': 'query', 'id': 'i2', 'q': 'items',
                'params': {'contains': 'Bulk Test Item'}})
            self.assertEqual(len(result['data']['definitions']), 50)
            self.assertTrue(result['data']['truncated'])

    async def test_is_admin_flips_live_with_group_membership(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_adm')
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'a1', 'q': 'is_admin',
                'params': {'name': char.name}})
            self.assertEqual(result['data'], {'is_admin': False})
            await sync_to_async(grant_admin)(char)
            result = await request(comm, {
                'type': 'query', 'id': 'a2', 'q': 'is_admin',
                'params': {'name': char.name}})
            self.assertEqual(result['data'], {'is_admin': True})


# ----------------------------------------------------------------------
# answer (§4.2, #273)
# ----------------------------------------------------------------------

class DoorAnswerTests(DoorTestBase):

    async def test_non_admin_target_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ans1')
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'n1', 'act': 'answer',
                'params': {'to': char.name, 'text': 'hello'}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-admin')

    async def test_online_delivery_sudo_category_and_records(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ans2')
        await sync_to_async(grant_admin)(char)
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'd1', 'act': 'answer',
                'params': {'to': char.name, 'text': 'the answer is 42'}})
            self.assertEqual(result['ok'], True)
            self.assertEqual(result['data'], {'delivered': True})
            self.assertEqual(len(layer.sent), 1)
            group, event = layer.sent[0]
            self.assertEqual(group, f'player_{char.pk}')
            self.assertEqual(event['type'], 'player_message')
            self.assertEqual(event['text'], 'sudo: the answer is 42')
            self.assertEqual(event['category'], 'sudo')
            self.assertIn('ts', event)
            # §6: the out record (audience = the target pk) plus the
            # agent_action record, both attributed to the agent.
            outs = door_records(fake, 'out')
            self.assertEqual(len(outs), 1)
            self.assertEqual(outs[0]['actor_name'], agent.username)
            self.assertEqual(json.loads(outs[0]['audience']), [char.pk])
            self.assertEqual(outs[0]['data']['category'], 'sudo')
            self.assertNotIn('ts', outs[0]['data'])
            actions = door_records(fake, 'agent_action')
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0]['data']['act'], 'answer')
            self.assertTrue(actions[0]['data']['ok'])
            self.assertEqual(actions[0]['data']['result'],
                             {'delivered': True})

    async def test_offline_is_ok_delivered_false(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ans3')
        await sync_to_async(grant_admin)(char)
        layer = RecordingLayer()
        async with self.door(agent, FakeDoorClient(), layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'o1', 'act': 'answer',
                'params': {'to': char.name, 'text': 'anyone home?'}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {'delivered': False})
            self.assertEqual(layer.sent, [])


# ----------------------------------------------------------------------
# gift (§4.2)
# ----------------------------------------------------------------------

class DoorGiftTests(DoorTestBase):

    async def test_gift_soulbinds_to_recipient_with_reward_line(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_gift')
        defn = await sync_to_async(make_equippable)(
            'door_gift', 'Test Iron Mace', 'weapon', ['MAIN_HAND'])
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'g1', 'act': 'gift',
                'params': {'to': char.name, 'slug': defn.slug,
                           'mk_tier': 1, 'rarity': 'uncommon'}})
            self.assertTrue(result['ok'])
            item = await sync_to_async(ItemInstance.objects.get)(
                pk=result['data']['item_id'])
            self.assertEqual(item.owner_id, char.pk)
            self.assertEqual(item.rarity, 'uncommon')
            self.assertEqual(item.mk_tier, 1)
            self.assertTrue(item.is_soulbound)
            self.assertEqual(item.soulbound_to_id, char.pk)
            group, event = layer.sent[0]
            self.assertEqual(group, f'player_{char.pk}')
            self.assertEqual(event['category'], 'reward')
            self.assertTrue(event['text'].startswith(
                'An admin has given you the Test Iron Mace'))

    async def test_artifact_rarity_requires_create(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_gifta')
        defn = await sync_to_async(make_equippable)(
            'door_gifta', 'Test Bauble', 'accessory', ['NECK'])
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'g2', 'act': 'gift',
                'params': {'to': char.name, 'slug': defn.slug,
                           'mk_tier': 1, 'rarity': 'artifact'}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'artifact-requires-create')

    async def test_mk_mismatch_surfaces_as_invalid_item(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_giftm')
        defn = await sync_to_async(make_equippable)(
            'door_giftm', 'Test Copper Rod', 'weapon', ['MAIN_HAND'],
            tier_material_mk_min=1, tier_material_mk_max=1)
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'g3', 'act': 'gift',
                'params': {'to': char.name, 'slug': defn.slug,
                           'mk_tier': 2, 'rarity': 'common'}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'invalid-item')
            self.assertIn('#211', result['detail'])

    async def test_gift_lands_over_capacity(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_giftc')

        def overfill():
            defn = make_equippable('door_giftc', 'Test Pebble', 'material', [])
            cap = carry_capacity(char, [])
            for _ in range(cap + 1):
                ItemInstance.objects.create(
                    definition=defn, owner=char, mk_tier=1, rarity='common')
            gift_defn = make_equippable('door_giftc', 'Test Overgift',
                                        'material', [])
            return cap, gift_defn
        cap, gift_defn = await sync_to_async(overfill)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'g4', 'act': 'gift',
                'params': {'to': char.name, 'slug': gift_defn.slug,
                           'mk_tier': 1, 'rarity': 'common'}})
            self.assertTrue(result['ok'],
                            'An admin gift lands regardless of carry state.')


# ----------------------------------------------------------------------
# create_artifact (§4.2, §5.4)
# ----------------------------------------------------------------------

def full_weapon_spec(name='Testfire Blade'):
    return {
        'name': name,
        'item_type': 'weapon',
        'description': 'A blade forged for the test of tests.',
        'genre_tag': 'fantasy',
        'mk_tier': 3,
        'base_value': 100,
        'valid_slots': ['MAIN_HAND'],
        'is_two_handed': False,
        'damage_midpoint': 12.5,
        'damage_spread': 3.0,
        'primary_stats': [{'stat': 'str', 'value': 5, 'floor': 4}],
        'secondary_stats': [{'stat': 'crit_chance', 'value': 2}],
    }


class DoorCreateArtifactTests(DoorTestBase):

    async def _create(self, comm, char, spec, frame_id='ca'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'create_artifact',
            'params': {'to': char.name, 'spec': spec}})

    async def test_full_spec_creates_soulbound_artifact(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_art')
        async with self.door(agent) as comm:
            result = await self._create(comm, char, full_weapon_spec())
            self.assertTrue(result['ok'])
            item = await sync_to_async(
                ItemInstance.objects.select_related('definition').get)(
                pk=result['data']['item_id'])
            defn = item.definition
            self.assertEqual(defn.name, 'Testfire Blade')
            self.assertEqual(defn.slug, 'testfire-blade')
            self.assertEqual(defn.scaling_base, 0.0)
            self.assertEqual(defn.scaling_factor, 0.0)
            self.assertFalse(defn.suppress_mk_suffix)
            self.assertEqual(item.rarity, ItemInstance.ARTIFACT)
            self.assertEqual(item.mk_tier, 3)
            self.assertTrue(item.is_soulbound)
            self.assertEqual(item.soulbound_to_id, char.pk)
            self.assertEqual(item.owner_id, char.pk)
            self.assertTrue(item.is_identified)
            self.assertEqual(item.damage_midpoint, 12.5)
            self.assertEqual(item.damage_spread, 3.0)
            self.assertEqual(item.rolled_primary_stats,
                             [{'stat': 'str', 'value': 5, 'floor': 4}])
            self.assertEqual(item.rolled_secondary_stats,
                             [{'stat': 'crit_chance', 'value': 2}])
            # The sell guard keys on exactly this field: cmd_sell refuses
            # rarity == 'artifact' (#138) — the door-built artifact is
            # unsellable by the same predicate the #138 tests pin.
            self.assertEqual(item.rarity, 'artifact')

    async def test_each_required_key_is_validated(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_artv')
        async with self.door(agent) as comm:
            for key in ('name', 'item_type', 'description', 'genre_tag',
                        'mk_tier', 'base_value', 'valid_slots',
                        'damage_midpoint', 'damage_spread'):
                spec = full_weapon_spec(f'Testfire {key}')
                del spec[key]
                result = await self._create(comm, char, spec, f'v-{key}')
                self.assertFalse(result['ok'], f'missing {key} must refuse')
                self.assertEqual(result['error'], 'bad-params',
                                 f'missing {key} must be bad-params')

    async def test_name_taken_case_insensitive(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_artn')
        await sync_to_async(make_equippable)(
            'door_artn', 'Taken Test Blade', 'weapon', ['MAIN_HAND'])
        async with self.door(agent) as comm:
            result = await self._create(
                comm, char, full_weapon_spec('taken test blade'))
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'name-taken')

    async def test_rarity_word_name_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_artr')
        async with self.door(agent) as comm:
            result = await self._create(
                comm, char, full_weapon_spec('Legendary Test Blade'))
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')

    async def test_mystery_pairing_enforced_and_applied(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_artm')
        async with self.door(agent) as comm:
            spec = full_weapon_spec('Testshroud Blade')
            spec['is_unidentifiable'] = True
            result = await self._create(comm, char, spec, 'm1')
            self.assertEqual(result['error'], 'bad-params')
            spec['mystery_name'] = 'a shrouded test blade'
            spec['mystery_description'] = 'Nothing about it can be known.'
            result = await self._create(comm, char, spec, 'm2')
            self.assertTrue(result['ok'])
            item = await sync_to_async(ItemInstance.objects.get)(
                pk=result['data']['item_id'])
            self.assertTrue(item.is_unidentifiable)
            self.assertFalse(item.is_identified)


# ----------------------------------------------------------------------
# strip / dress (§4.2)
# ----------------------------------------------------------------------

class DoorStripDressTests(DoorTestBase):

    def _gear_up(self, char):
        """Two equipped pieces; the armor carries +5 end so gear moves
        the bar maxima. Vitality pinned to a clean half-full fraction."""
        weapon = make_equippable('door_sd', 'Test Saber', 'weapon',
                                 ['MAIN_HAND'])
        armor = make_equippable('door_sd', 'Test Cuirass', 'armor',
                                ['CHEST'])
        saber = ItemInstance.objects.create(
            definition=weapon, owner=char, mk_tier=1, rarity='common',
            is_equipped=True, equipped_slot='MAIN_HAND')
        cuirass = ItemInstance.objects.create(
            definition=armor, owner=char, mk_tier=1, rarity='common',
            is_equipped=True, equipped_slot='CHEST',
            rolled_primary_stats=[{'stat': 'end', 'value': 5}])
        Character.objects.filter(pk=char.pk).update(
            vitality_current=50, vitality_max=100,
            longevity_current=30, longevity_max=100)
        return saber, cuirass

    def _fractions(self, char):
        char.refresh_from_db()
        return (char.vitality_current / char.vitality_max,
                char.longevity_current / char.longevity_max)

    async def test_strip_snapshots_before_unequip_and_keeps_fractions(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_sd1')
        saber, cuirass = await sync_to_async(self._gear_up)(char)
        vit_before, lon_before = await sync_to_async(self._fractions)(char)
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 's1', 'act': 'strip',
                'params': {'name': char.name}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {'stripped': 2})

        def state():
            char.refresh_from_db()
            saber.refresh_from_db()
            cuirass.refresh_from_db()
            return char.outfit_snapshot
        snapshot = await sync_to_async(state)()
        # The snapshot holds the pre-unequip slots — post-strip the
        # instances carry '' — so it was written before the loop.
        self.assertEqual(
            sorted(snapshot, key=lambda e: e['instance_id']),
            sorted([{'instance_id': saber.pk, 'slot': 'MAIN_HAND'},
                    {'instance_id': cuirass.pk, 'slot': 'CHEST'}],
                   key=lambda e: e['instance_id']))
        self.assertFalse(saber.is_equipped)
        self.assertEqual(saber.equipped_slot, '')
        self.assertFalse(cuirass.is_equipped)
        # The bar law: fill fraction invariant under the gear mutation.
        vit_after, lon_after = await sync_to_async(self._fractions)(char)
        self.assertLess(abs(vit_after - vit_before), 0.01)
        self.assertLess(abs(lon_after - lon_before), 0.01)

    async def test_dress_round_trip_restores_exact_slots_and_consumes(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_sd2')
        saber, cuirass = await sync_to_async(self._gear_up)(char)
        async with self.door(agent) as comm:
            await request(comm, {
                'type': 'action', 'id': 's1', 'act': 'strip',
                'params': {'name': char.name}})
            vit_mid, lon_mid = await sync_to_async(self._fractions)(char)
            result = await request(comm, {
                'type': 'action', 'id': 'd1', 'act': 'dress',
                'params': {'name': char.name}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {'restored': 2, 'missing': []})

        def state():
            char.refresh_from_db()
            saber.refresh_from_db()
            cuirass.refresh_from_db()
        await sync_to_async(state)()
        self.assertTrue(saber.is_equipped)
        self.assertEqual(saber.equipped_slot, 'MAIN_HAND')
        self.assertTrue(cuirass.is_equipped)
        self.assertEqual(cuirass.equipped_slot, 'CHEST')
        # Byte-consistent with equip_item: dress re-soulbinds.
        self.assertTrue(saber.is_soulbound)
        self.assertEqual(saber.soulbound_to_id, char.pk)
        # Snapshot consumed.
        self.assertIsNone(char.outfit_snapshot)
        vit_after, lon_after = await sync_to_async(self._fractions)(char)
        self.assertLess(abs(vit_after - vit_mid), 0.01)
        self.assertLess(abs(lon_after - lon_mid), 0.01)

    async def test_dress_reports_missing_and_still_consumes(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_sd3')
        saber, cuirass = await sync_to_async(self._gear_up)(char)
        async with self.door(agent) as comm:
            await request(comm, {
                'type': 'action', 'id': 's1', 'act': 'strip',
                'params': {'name': char.name}})
            saber_pk = saber.pk
            await sync_to_async(saber.delete)()
            result = await request(comm, {
                'type': 'action', 'id': 'd1', 'act': 'dress',
                'params': {'name': char.name}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'restored': 1, 'missing': [saber_pk]})
        snapshot = await sync_to_async(
            lambda: Character.objects.values_list(
                'outfit_snapshot', flat=True).get(pk=char.pk))()
        self.assertIsNone(snapshot)

    async def test_nothing_equipped_and_no_outfit_errors(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_sd4')
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 's1', 'act': 'strip',
                'params': {'name': char.name}})
            self.assertEqual(result['error'], 'nothing-equipped')
            result = await request(comm, {
                'type': 'action', 'id': 'd1', 'act': 'dress',
                'params': {'name': char.name}})
            self.assertEqual(result['error'], 'no-outfit')

    async def test_online_strip_sends_narration_with_refresh_event(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_sd5')
        await sync_to_async(self._gear_up)(char)
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            await request(comm, {
                'type': 'action', 'id': 's1', 'act': 'strip',
                'params': {'name': char.name}})
            group, event = layer.sent[0]
            self.assertEqual(group, f'player_{char.pk}')
            self.assertEqual(
                event['text'],
                'An admin has unequipped your gear; it is in your inventory.')
            self.assertEqual(event['category'], 'system')
            self.assertEqual(event['event'], 'refresh_status')


# ----------------------------------------------------------------------
# move (§4.2)
# ----------------------------------------------------------------------

class DoorMoveTests(DoorTestBase):

    async def test_offline_move_updates_db_and_visit_no_broadcasts(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_mv1')
        layer = RecordingLayer()
        async with self.door(agent, FakeDoorClient(), layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'm1', 'act': 'move',
                'params': {'name': char.name, 'to_room_id': room_b.id}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['room']['id'], room_b.id)
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, room_b.id)
        visited = await sync_to_async(RoomVisit.objects.filter(
            character=char, room=room_b).exists)()
        self.assertTrue(visited, 'Offline move records the visit door-side.')
        self.assertEqual(layer.sent, [])

    async def test_online_move_broadcasts_and_defers_visit_to_consumer(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_mv2')
        other = await sync_to_async(make_character)('door_mv2b', room_b)
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'm1', 'act': 'move',
                'params': {'name': char.name, 'to_name': other.name}})
            self.assertTrue(result['ok'])
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, room_b.id)
        # Visit deferred to the consumer's moved branch (the respawn
        # division of labor) so a first visit can announce completion.
        visited = await sync_to_async(RoomVisit.objects.filter(
            character=char, room=room_b).exists)()
        self.assertFalse(visited)
        sends = {group: event for group, event in layer.sent}
        left = sends[f'room_{room_a.id}']
        self.assertEqual(left['text'], f'{char.name} has left.')
        self.assertEqual(left['exclude_pk'], char.pk)
        arrived = sends[f'room_{room_b.id}']
        self.assertEqual(arrived['text'], f'{char.name} has arrived.')
        self.assertEqual(arrived['exclude_pk'], char.pk)
        moved = sends[f'player_{char.pk}']
        self.assertEqual(moved['event'], 'moved')
        self.assertEqual(moved['text'], 'An admin moved you to a new room.')
        self.assertEqual(moved['category'], 'system')

    async def test_in_combat_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_mv3')

        def engage():
            session = CombatSession.objects.create(room=room_a)
            session.characters.add(char)
        await sync_to_async(engage)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'm1', 'act': 'move',
                'params': {'name': char.name, 'to_room_id': room_b.id}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'in-combat')

    async def test_exactly_one_destination_required(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_mv4')
        async with self.door(agent) as comm:
            for params in (
                {'name': char.name},
                {'name': char.name, 'to_room_id': room_b.id,
                 'to_name': char.name},
            ):
                result = await request(comm, {
                    'type': 'action', 'id': 'm1', 'act': 'move',
                    'params': params})
                self.assertEqual(result['error'], 'bad-params')


class MovedBranchTests(TransactionTestCase):
    """The consumer's moved branch end-to-end (the respawn shape from
    test_room_visits.py — requires the in-container environment)."""

    async def _drain_until_map(self, communicator):
        room_texts = []
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            if msg.get('type') == 'map':
                return room_texts
            if (msg.get('type') == 'output'
                    and msg.get('category') == 'room-render'
                    and msg.get('exits') is not None):
                room_texts.append(msg['room_text'])

    async def test_moved_event_reseats_records_visit_and_renders(self):
        zone, room_a, room_b = await sync_to_async(make_world)('DoorMoved')
        character = await sync_to_async(make_character)('DoorMoved', room_a)
        communicator = WebsocketCommunicator(
            SkylandConsumer.as_asgi(), '/ws/shyland/')
        communicator.scope['user'] = character.user
        connected, _ = await communicator.connect()
        assert connected
        await self._drain_until_map(communicator)
        try:
            # Simulate the door: DB move, then the audited moved event.
            await sync_to_async(
                Character.objects.filter(pk=character.pk).update
            )(current_room=room_b)
            await get_channel_layer().group_send(f'player_{character.pk}', {
                'type': 'player_message',
                'event': 'moved',
                'text': 'An admin moved you to a new room.',
                'category': 'system',
            })
            texts = await self._drain_until_map(communicator)
            visit_exists = await sync_to_async(RoomVisit.objects.filter(
                character=character, room=room_b).exists)()
            self.assertTrue(
                visit_exists,
                'The moved branch must record the arrival visit.')
            self.assertEqual(len(texts), 1)
            self.assertIn('The long form of room B.', texts[0])
        finally:
            await communicator.disconnect()


# ----------------------------------------------------------------------
# Name reservation (§7.7, GDD §3)
# ----------------------------------------------------------------------

class BotNameReservationTests(TestCase):

    def setUp(self):
        self.origin = Origin.objects.create(
            name='Res Origin', slug='res-origin',
            acuity_baseline=1.0, acuity_band_low=0.8, acuity_band_high=1.2)
        self.archetype = Archetype.objects.create(
            name='Res Archetype', slug='res-archetype',
            primary_stat_1='str', primary_stat_2='dex')

    def _form(self, name):
        return CharacterCreationForm(data={
            'origin': self.origin.pk, 'archetype': self.archetype.pk,
            'name': name})

    def test_reserved_names_refused_case_insensitively(self):
        for name in ('sudo', 'Sudo', 'SUDO', 'sirius', 'Sirius'):
            form = self._form(name)
            self.assertFalse(form.is_valid(), f'{name!r} must be refused')
            self.assertIn('That name belongs to the world already.',
                          form.errors['name'])

    def test_unreserved_name_still_passes(self):
        form = self._form('Resthorne')
        self.assertTrue(form.is_valid(), form.errors)

    def test_no_existing_character_or_npc_holds_a_reserved_name(self):
        # §7.7: the implementation-time collision check, pinned.
        for name in RESERVED_BOT_NAMES:
            self.assertFalse(
                Character.objects.filter(name__iexact=name).exists())
            self.assertFalse(
                NpcDefinition.objects.filter(name__iexact=name).exists())


# ----------------------------------------------------------------------
# Granular item control (v25.7 — #287/#288/#289/#293)
# ----------------------------------------------------------------------

def make_carried(prefix, char, name, item_type='accessory', slots=None,
                 **inst_kwargs):
    """One owned instance over its own definition."""
    defn = make_equippable(prefix, name, item_type,
                           ['NECK'] if slots is None else slots)
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity='common',
        **inst_kwargs)


def make_cursed(prefix, char, item):
    """Wire a live curse onto an instance the way the admin would:
    ``active_curse`` is admin-set data (no code path populates it)."""
    effect_defn = EffectDefinition.objects.create(
        name=f'{prefix} Test Curse', slug=f'{prefix}-test-curse')
    component = EffectComponent.objects.create(
        definition=effect_defn, component_type='curse_generic',
        magnitude_base=1.0)
    instance = EffectInstance.objects.create(
        definition=effect_defn, target=char)
    EffectComponentInstance.objects.create(
        effect_instance=instance, component=component, magnitude=1.0)
    item.is_cursed = True
    item.active_curse = instance
    item.save()
    return instance


def pin_bars(char):
    """The strip/dress bar-law fixture shape: clean fractions."""
    Character.objects.filter(pk=char.pk).update(
        vitality_current=50, vitality_max=100,
        longevity_current=30, longevity_max=100)


def bar_fractions(char):
    char.refresh_from_db()
    return (char.vitality_current / char.vitality_max,
            char.longevity_current / char.longevity_max)


class DoorInventoryQueryTests(DoorTestBase):

    async def test_roster_equipped_and_carried_uncapped(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_inv')

        def build():
            worn = make_carried('door_inv', char, 'Test Torc',
                                is_equipped=True, equipped_slot='NECK')
            bulk_defn = make_equippable('door_inv', 'Test Invpebble',
                                        'material', [])
            carried = [
                ItemInstance.objects.create(
                    definition=bulk_defn, owner=char, mk_tier=1,
                    rarity='common')
                for _ in range(51)
            ]
            return worn, carried
        worn, carried = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'i1', 'q': 'inventory',
                'params': {'name': char.name}})
            self.assertTrue(result['ok'])
            data = result['data']
            self.assertEqual(data['character_id'], char.pk)
            self.assertEqual(data['character_name'], char.name)
            # Uncapped: 52 > ITEMS_CAP, every instance present.
            self.assertEqual(data['count'], 52)
            self.assertEqual(len(data['items']), 52)
            self.assertNotIn('truncated', data)
            rows = {row['id']: row for row in data['items']}
            self.assertEqual(set(rows),
                             {worn.pk} | {i.pk for i in carried})
            worn_row = rows[worn.pk]
            self.assertEqual(worn_row['name'], 'Test Torc')
            self.assertEqual(worn_row['item_type'], 'accessory')
            self.assertEqual(worn_row['mk_tier'], 1)
            self.assertEqual(worn_row['rarity'], 'common')
            self.assertEqual(worn_row['durability_current'], 100.0)
            self.assertFalse(worn_row['is_broken'])
            self.assertFalse(worn_row['is_soulbound'])
            self.assertTrue(worn_row['is_equipped'])
            self.assertEqual(worn_row['equipped_slot'], 'NECK')
            carried_row = rows[carried[0].pk]
            self.assertFalse(carried_row['is_equipped'])
            self.assertEqual(carried_row['equipped_slot'], '')

    async def test_unknown_character_not_found(self):
        agent = await sync_to_async(make_agent)('door_inv2')
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'i1', 'q': 'inventory',
                'params': {'name': 'Nobody Such'}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')

    async def test_empty_inventory_count_zero(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_inv3')
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'i1', 'q': 'inventory',
                'params': {'name': char.name}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['count'], 0)
            self.assertEqual(result['data']['items'], [])


class DoorItemQueryTests(DoorTestBase):

    async def test_full_fidelity_true_state(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_itq')

        def build():
            item = make_carried(
                'door_itq', char, 'Test Veiled Band',
                rolled_primary_stats=[{'stat': 'str', 'value': 3}],
                rolled_secondary_stats=[{'stat': 'crit_chance', 'value': 1}],
                is_identified=False, is_unidentifiable=True)
            make_cursed('door_itq', char, item)
            return item
        item = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'q1', 'q': 'item',
                'params': {'item_id': item.pk}})
            self.assertTrue(result['ok'])
            data = result['data']
            # True state: the definition's real name despite the veil,
            # curse and identification flags exactly as stored.
            self.assertEqual(data['name'], 'Test Veiled Band')
            self.assertEqual(data['rolled_primary_stats'],
                             [{'stat': 'str', 'value': 3}])
            self.assertEqual(data['rolled_secondary_stats'],
                             [{'stat': 'crit_chance', 'value': 1}])
            self.assertIsNone(data['damage_midpoint'])
            self.assertIsNone(data['damage_spread'])
            self.assertTrue(data['is_cursed'])
            self.assertFalse(data['curse_identified'])
            self.assertFalse(data['is_identified'])
            self.assertTrue(data['is_unidentifiable'])
            self.assertEqual(data['owner'],
                             {'id': char.pk, 'name': char.name})
            self.assertIsNone(data['room'])

    async def test_room_floor_instance_owner_null_room_present(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_itq2')

        def build():
            defn = make_equippable('door_itq2', 'Test Floor Coin',
                                   'material', [])
            return ItemInstance.objects.create(
                definition=defn, current_room=room_a, mk_tier=1,
                rarity='common')
        item = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'q1', 'q': 'item',
                'params': {'item_id': item.pk}})
            self.assertTrue(result['ok'])
            self.assertIsNone(result['data']['owner'])
            self.assertEqual(result['data']['room']['id'], room_a.id)
            self.assertEqual(result['data']['room']['zone'], zone.name)

    async def test_unknown_id_not_found(self):
        agent = await sync_to_async(make_agent)('door_itq3')
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'query', 'id': 'q1', 'q': 'item',
                'params': {'item_id': 999999}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')


class DoorItemWriteAddressingTests(DoorTestBase):
    """The §4 shared addressing law across every write kind."""

    WRITE_FRAMES = (
        ('remove_item', {}),
        ('edit_item', {'changes': {'mk_tier': 2}}),
        ('equip_item', {}),
        ('unequip_item', {}),
    )

    async def test_wrong_owner_refused_on_every_write_kind(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_own')
        other = await sync_to_async(make_character)('door_own2', room_b)
        item = await sync_to_async(make_carried)(
            'door_own', other, 'Test Other Band')
        floor = await sync_to_async(
            lambda: ItemInstance.objects.create(
                definition=make_equippable('door_own', 'Test Floor Band',
                                           'accessory', ['NECK']),
                current_room=room_a, mk_tier=1, rarity='common'))()
        async with self.door(agent) as comm:
            for act, extra in self.WRITE_FRAMES:
                for target, state_word in ((item, other.name),
                                           (floor, 'no character')):
                    result = await request(comm, {
                        'type': 'action', 'id': f'{act}-{target.pk}',
                        'act': act,
                        'params': dict({'name': char.name,
                                        'item_id': target.pk}, **extra)})
                    self.assertFalse(result['ok'], act)
                    self.assertEqual(result['error'], 'not-owner', act)
                    # The detail names the actual state.
                    self.assertIn(state_word, result['detail'], act)

    async def test_stale_id_not_found_on_every_write_kind(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_stale')
        async with self.door(agent) as comm:
            for act, extra in self.WRITE_FRAMES:
                result = await request(comm, {
                    'type': 'action', 'id': f's-{act}', 'act': act,
                    'params': dict({'name': char.name, 'item_id': 999999},
                                   **extra)})
                self.assertFalse(result['ok'], act)
                self.assertEqual(result['error'], 'not-found', act)

    async def test_malformed_params_bad_params(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_mal')
        item = await sync_to_async(make_carried)(
            'door_mal', char, 'Test Malformed Band')
        async with self.door(agent) as comm:
            frames = (
                # item_id missing / non-int.
                {'act': 'remove_item', 'params': {'name': char.name}},
                {'act': 'remove_item',
                 'params': {'name': char.name, 'item_id': 'seven'}},
                # changes missing / empty / not an object.
                {'act': 'edit_item',
                 'params': {'name': char.name, 'item_id': item.pk}},
                {'act': 'edit_item',
                 'params': {'name': char.name, 'item_id': item.pk,
                            'changes': {}}},
                {'act': 'edit_item',
                 'params': {'name': char.name, 'item_id': item.pk,
                            'changes': 'mk_tier'}},
                # slot present but not a string.
                {'act': 'equip_item',
                 'params': {'name': char.name, 'item_id': item.pk,
                            'slot': 7}},
                # character name missing.
                {'act': 'unequip_item', 'params': {'item_id': item.pk}},
            )
            for n, frame in enumerate(frames):
                result = await request(comm, {
                    'type': 'action', 'id': f'm{n}', 'act': frame['act'],
                    'params': frame['params']})
                self.assertFalse(result['ok'], frame)
                self.assertEqual(result['error'], 'bad-params', frame)


class DoorRemoveItemTests(DoorTestBase):

    async def _create_artifact(self, comm, char, spec, frame_id='ca'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'create_artifact',
            'params': {'to': char.name, 'spec': spec}})

    async def test_ordinary_removal_definition_survives(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_rm1')
        item = await sync_to_async(make_carried)(
            'door_rm1', char, 'Test Doomed Band')
        defn_pk = item.definition_id
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'r1', 'act': 'remove_item',
                'params': {'name': char.name, 'item_id': item.pk}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'item_id': item.pk,
                              'definition_removed': False})
        self.assertFalse(await sync_to_async(
            ItemInstance.objects.filter(pk=item.pk).exists)())
        self.assertTrue(await sync_to_async(
            ItemDefinition.objects.filter(pk=defn_pk).exists)())

    async def test_artifact_removal_frees_the_name(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_rm2')
        async with self.door(agent) as comm:
            spec = full_weapon_spec('Test Reforged Blade')
            result = await self._create_artifact(comm, char, spec, 'c1')
            self.assertTrue(result['ok'])
            item_id = result['data']['item_id']
            defn_id = result['data']['definition_id']
            result = await request(comm, {
                'type': 'action', 'id': 'r1', 'act': 'remove_item',
                'params': {'name': char.name, 'item_id': item_id}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'item_id': item_id,
                              'definition_removed': True})
            self.assertFalse(await sync_to_async(
                ItemDefinition.objects.filter(pk=defn_id).exists)())
            self.assertFalse(await sync_to_async(
                ItemInstance.objects.filter(pk=item_id).exists)())
            # The freed-name law: the same name creates again.
            result = await self._create_artifact(comm, char, spec, 'c2')
            self.assertTrue(result['ok'],
                            'Removed artifact name must be re-authorable.')

    async def test_equipped_target_rescales_bars(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_rm3')

        def build():
            item = make_carried(
                'door_rm3', char, 'Test End Cuirass', item_type='armor',
                slots=['CHEST'], is_equipped=True, equipped_slot='CHEST',
                rolled_primary_stats=[{'stat': 'end', 'value': 5}])
            pin_bars(char)
            return item
        item = await sync_to_async(build)()
        vit_before, lon_before = await sync_to_async(bar_fractions)(char)
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'r1', 'act': 'remove_item',
                'params': {'name': char.name, 'item_id': item.pk}})
            self.assertTrue(result['ok'])
        # The bar law: fill fraction invariant under the max change.
        vit_after, lon_after = await sync_to_async(bar_fractions)(char)
        self.assertLess(abs(vit_after - vit_before), 0.01)
        self.assertLess(abs(lon_after - lon_before), 0.01)

    async def test_cursed_target_curse_ends_with_the_item(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_rm4')

        def build():
            item = make_carried('door_rm4', char, 'Test Cursed Band')
            curse = make_cursed('door_rm4', char, item)
            return item, curse
        item, curse = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'r1', 'act': 'remove_item',
                'params': {'name': char.name, 'item_id': item.pk}})
            self.assertTrue(result['ok'])

        def state():
            curse.refresh_from_db()
            component = curse.component_instances.get()
            return (curse.is_active, curse.removed_by,
                    component.is_active, component.removed_by)
        ei_active, ei_by, ci_active, ci_by = await sync_to_async(state)()
        self.assertFalse(ei_active)
        self.assertEqual(ei_by, 'item-removed')
        self.assertFalse(ci_active)
        self.assertEqual(ci_by, 'item-removed')

    async def test_online_narration_events_and_offline_silence(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_rm5')

        def build():
            carried = make_carried('door_rm5', char, 'Test Plain Band')
            worn = make_carried(
                'door_rm5', char, 'Test Worn Band', slots=['NECK'],
                is_equipped=True, equipped_slot='NECK')
            return carried, worn
        carried, worn = await sync_to_async(build)()
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            await request(comm, {
                'type': 'action', 'id': 'r1', 'act': 'remove_item',
                'params': {'name': char.name, 'item_id': carried.pk}})
            group, event = layer.sent[0]
            self.assertEqual(group, f'player_{char.pk}')
            self.assertEqual(
                event['text'],
                'An admin has taken the Test Plain Band Mk 1 from you.')
            self.assertEqual(event['category'], 'system')
            # Unequipped target: no status refresh rides along.
            self.assertNotIn('event', event)
            await request(comm, {
                'type': 'action', 'id': 'r2', 'act': 'remove_item',
                'params': {'name': char.name, 'item_id': worn.pk}})
            group, event = layer.sent[1]
            self.assertEqual(event['event'], 'refresh_status')
        # Offline: the mutation lands silently.
        other = await sync_to_async(make_character)('door_rm5b', room_b)
        silent = await sync_to_async(make_carried)(
            'door_rm5', other, 'Test Silent Band')
        layer2 = RecordingLayer()
        async with self.door(agent, FakeDoorClient(), layer2) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'r3', 'act': 'remove_item',
                'params': {'name': other.name, 'item_id': silent.pk}})
            self.assertTrue(result['ok'])
            self.assertEqual(layer2.sent, [])


class DoorEditItemTests(DoorTestBase):

    async def _create_artifact(self, comm, char, spec, frame_id='ca'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'create_artifact',
            'params': {'to': char.name, 'spec': spec}})

    async def _edit(self, comm, char, item_id, changes, frame_id='e1'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'edit_item',
            'params': {'name': char.name, 'item_id': item_id,
                       'changes': changes}})

    async def test_mk_tier_raw_set_lands(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ed1')
        item = await sync_to_async(make_carried)(
            'door_ed1', char, 'Test Tunable Band',
            rolled_primary_stats=[{'stat': 'str', 'value': 3}])
        async with self.door(agent) as comm:
            result = await self._edit(comm, char, item.pk, {'mk_tier': 3})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'item_id': item.pk, 'changed': ['mk_tier'],
                              'definition_changed': False})
        await sync_to_async(item.refresh_from_db)()
        self.assertEqual(item.mk_tier, 3)
        # Raw set: nothing re-rolls.
        self.assertEqual(item.rolled_primary_stats,
                         [{'stat': 'str', 'value': 3}])

    async def test_unknown_key_refuses_whole(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ed2')
        item = await sync_to_async(make_carried)(
            'door_ed2', char, 'Test Guarded Band')
        async with self.door(agent) as comm:
            result = await self._edit(
                comm, char, item.pk, {'mk_tier': 5, 'bogus_key': 1})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('bogus_key', result['detail'])
        await sync_to_async(item.refresh_from_db)()
        # No partial application: the whitelisted key did not land.
        self.assertEqual(item.mk_tier, 1)

    async def test_definition_key_on_non_artifact_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ed3')
        item = await sync_to_async(make_carried)(
            'door_ed3', char, 'Test Template Band')
        async with self.door(agent) as comm:
            result = await self._edit(
                comm, char, item.pk, {'name': 'Test Renamed Band'})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-artifact')

    async def test_artifact_rename_collision_and_self_rename(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ed4')
        await sync_to_async(make_equippable)(
            'door_ed4', 'Test Occupied Blade', 'weapon', ['MAIN_HAND'])
        async with self.door(agent) as comm:
            result = await self._create_artifact(
                comm, char, full_weapon_spec('Test Protean Blade'))
            self.assertTrue(result['ok'])
            item_id = result['data']['item_id']
            defn_id = result['data']['definition_id']
            # Rename: name and slug both move.
            result = await self._edit(
                comm, char, item_id, {'name': 'Test Shifted Blade'}, 'e1')
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'item_id': item_id, 'changed': ['name'],
                              'definition_changed': True})
            defn = await sync_to_async(ItemDefinition.objects.get)(pk=defn_id)
            self.assertEqual(defn.name, 'Test Shifted Blade')
            self.assertEqual(defn.slug, 'test-shifted-blade')
            # Collision (case-insensitive) refuses.
            result = await self._edit(
                comm, char, item_id, {'name': 'test occupied blade'}, 'e2')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'name-taken')
            # Self-rename to the same name is allowed.
            result = await self._edit(
                comm, char, item_id, {'name': 'Test Shifted Blade'}, 'e3')
            self.assertTrue(result['ok'])

    async def test_durability_zero_sets_broken(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ed5')
        item = await sync_to_async(make_carried)(
            'door_ed5', char, 'Test Brittle Band')
        async with self.door(agent) as comm:
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 0})
            self.assertTrue(result['ok'])
            await sync_to_async(item.refresh_from_db)()
            self.assertEqual(item.durability_current, 0.0)
            self.assertTrue(item.is_broken)
            # v25.12 (#314): durability is integral — the fractional
            # value this test once pinned as accepted is now refused;
            # the nonzero-clears-broken intent rides a whole number.
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 40.5}, 'e2')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 40}, 'e3')
            self.assertTrue(result['ok'])
            await sync_to_async(item.refresh_from_db)()
            self.assertEqual(item.durability_current, 40.0)
            self.assertFalse(item.is_broken)

    async def test_equipped_edit_rescales_bars_and_refreshes(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_ed6')

        def build():
            item = make_carried(
                'door_ed6', char, 'Test Growth Cuirass', item_type='armor',
                slots=['CHEST'], is_equipped=True, equipped_slot='CHEST',
                rolled_primary_stats=[{'stat': 'end', 'value': 5}])
            pin_bars(char)
            return item
        item = await sync_to_async(build)()
        vit_before, lon_before = await sync_to_async(bar_fractions)(char)
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await self._edit(
                comm, char, item.pk,
                {'rolled_primary_stats': [{'stat': 'end', 'value': 25}]})
            self.assertTrue(result['ok'])
            group, event = layer.sent[0]
            self.assertEqual(
                event['text'],
                'An admin has altered the Test Growth Cuirass Mk 1.')
            self.assertEqual(event['event'], 'refresh_status')
        vit_after, lon_after = await sync_to_async(bar_fractions)(char)
        self.assertLess(abs(vit_after - vit_before), 0.01)
        self.assertLess(abs(lon_after - lon_before), 0.01)
        await sync_to_async(item.refresh_from_db)()
        self.assertEqual(item.rolled_primary_stats,
                         [{'stat': 'end', 'value': 25}])


class DoorEquipItemTests(DoorTestBase):

    async def _equip(self, comm, char, item_id, slot=None, frame_id='q1'):
        params = {'name': char.name, 'item_id': item_id}
        if slot is not None:
            params['slot'] = slot
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'equip_item',
            'params': params})

    async def test_free_slot_auto(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq1')
        item = await sync_to_async(make_carried)(
            'door_eq1', char, 'Test Free Torc')
        async with self.door(agent) as comm:
            result = await self._equip(comm, char, item.pk)
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'item_id': item.pk, 'slot': 'NECK',
                              'displaced': []})
        await sync_to_async(item.refresh_from_db)()
        self.assertTrue(item.is_equipped)
        self.assertEqual(item.equipped_slot, 'NECK')

    async def test_explicit_slot_displaces_that_occupant(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq2')

        def build():
            occupant = make_carried(
                'door_eq2', char, 'Test Neck Holder', slots=['NECK'],
                is_equipped=True, equipped_slot='NECK')
            item = make_carried('door_eq2', char, 'Test Twin Band',
                                slots=['NECK', 'WAIST'])
            return occupant, item
        occupant, item = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await self._equip(comm, char, item.pk, slot='NECK')
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'item_id': item.pk, 'slot': 'NECK',
                              'displaced': [occupant.pk]})

        def state():
            occupant.refresh_from_db()
            item.refresh_from_db()
        await sync_to_async(state)()
        self.assertFalse(occupant.is_equipped)
        self.assertEqual(occupant.equipped_slot, '')
        self.assertTrue(item.is_equipped)
        self.assertEqual(item.equipped_slot, 'NECK')

    async def test_invalid_slot_and_unequippable(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq3')
        item = await sync_to_async(make_carried)(
            'door_eq3', char, 'Test Slotted Torc')
        lump = await sync_to_async(make_carried)(
            'door_eq3', char, 'Test Slotless Lump', item_type='material',
            slots=[])
        async with self.door(agent) as comm:
            result = await self._equip(comm, char, item.pk, slot='HEAD')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-slot')
            self.assertIn('NECK', result['detail'])
            result = await self._equip(comm, char, lump.pk, frame_id='q2')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-slot')

    async def test_two_rings_full_is_ambiguous_naming_both(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq4')

        def build():
            ring_defn = make_equippable('door_eq4', 'Test Ring',
                                        'accessory', ['RING'])
            worn = [
                ItemInstance.objects.create(
                    definition=ring_defn, owner=char, mk_tier=1,
                    rarity='common', is_equipped=True, equipped_slot='RING')
                for _ in range(2)
            ]
            third = ItemInstance.objects.create(
                definition=ring_defn, owner=char, mk_tier=1, rarity='common')
            return worn, third
        worn, third = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await self._equip(comm, char, third.pk)
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'ambiguous')
            # Structured enough to act on: both options named with ids.
            for option in worn:
                self.assertIn(f'(id {option.pk})', result['detail'])
        await sync_to_async(third.refresh_from_db)()
        self.assertFalse(third.is_equipped)

    async def test_displaces_cursed_occupant_admin_style(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq5')

        def build():
            occupant = make_carried(
                'door_eq5', char, 'Test Cursed Holder', slots=['NECK'],
                is_equipped=True, equipped_slot='NECK', is_cursed=True)
            item = make_carried('door_eq5', char, 'Test Clean Torc')
            return occupant, item
        occupant, item = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await self._equip(comm, char, item.pk)
            self.assertTrue(
                result['ok'],
                'Protective guards yield admin-side: cursed comes off.')
            self.assertEqual(result['data']['displaced'], [occupant.pk])
        await sync_to_async(occupant.refresh_from_db)()
        self.assertFalse(occupant.is_equipped)

    async def test_two_hander_displaces_both_hands(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq6')

        def build():
            main = make_carried(
                'door_eq6', char, 'Test Main Saber', item_type='weapon',
                slots=['MAIN_HAND'], is_equipped=True,
                equipped_slot='MAIN_HAND')
            off = make_carried(
                'door_eq6', char, 'Test Off Dagger', item_type='weapon',
                slots=['OFF_HAND'], is_equipped=True,
                equipped_slot='OFF_HAND')
            two_hander_defn = make_equippable(
                'door_eq6', 'Test Great Maul', 'weapon', ['MAIN_HAND'],
                is_two_handed=True)
            maul = ItemInstance.objects.create(
                definition=two_hander_defn, owner=char, mk_tier=1,
                rarity='common')
            return main, off, maul
        main, off, maul = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await self._equip(comm, char, maul.pk)
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['slot'], 'MAIN_HAND')
            self.assertEqual(set(result['data']['displaced']),
                             {main.pk, off.pk})

        def state():
            main.refresh_from_db()
            off.refresh_from_db()
            maul.refresh_from_db()
        await sync_to_async(state)()
        self.assertFalse(main.is_equipped)
        self.assertFalse(off.is_equipped)
        self.assertTrue(maul.is_equipped)

    async def test_re_soulbind_snapshot_untouched_and_narration(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq7')
        sentinel = [{'instance_id': 999999, 'slot': 'HEAD'}]

        def build():
            item = make_carried('door_eq7', char, 'Test Binding Torc')
            Character.objects.filter(pk=char.pk).update(
                outfit_snapshot=sentinel)
            return item
        item = await sync_to_async(build)()
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await self._equip(comm, char, item.pk)
            self.assertTrue(result['ok'])
            group, event = layer.sent[0]
            self.assertEqual(
                event['text'],
                'An admin has equipped the Test Binding Torc Mk 1 on you.')
            self.assertEqual(event['event'], 'refresh_status')

        def state():
            item.refresh_from_db()
            char.refresh_from_db()
        await sync_to_async(state)()
        # Byte-consistent with equip_item/_dress: equip re-soulbinds.
        self.assertTrue(item.is_soulbound)
        self.assertEqual(item.soulbound_to_id, char.pk)
        # outfit_snapshot is never read, written, or consumed.
        self.assertEqual(char.outfit_snapshot, sentinel)

    async def test_already_equipped_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_eq8')
        item = await sync_to_async(make_carried)(
            'door_eq8', char, 'Test Settled Torc', is_equipped=True,
            equipped_slot='NECK')
        async with self.door(agent) as comm:
            result = await self._equip(comm, char, item.pk)
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'already-equipped')


class DoorUnequipItemTests(DoorTestBase):

    async def _unequip(self, comm, char, item_id, frame_id='u1'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'unequip_item',
            'params': {'name': char.name, 'item_id': item_id}})

    async def test_happy_path_with_narration_and_snapshot_untouched(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_uq1')
        sentinel = [{'instance_id': 999999, 'slot': 'HEAD'}]

        def build():
            item = make_carried(
                'door_uq1', char, 'Test Shed Cuirass', item_type='armor',
                slots=['CHEST'], is_equipped=True, equipped_slot='CHEST',
                rolled_primary_stats=[{'stat': 'end', 'value': 5}])
            Character.objects.filter(pk=char.pk).update(
                outfit_snapshot=sentinel)
            pin_bars(char)
            return item
        item = await sync_to_async(build)()
        vit_before, lon_before = await sync_to_async(bar_fractions)(char)
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await self._unequip(comm, char, item.pk)
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {'item_id': item.pk})
            group, event = layer.sent[0]
            self.assertEqual(
                event['text'],
                'An admin has unequipped the Test Shed Cuirass Mk 1; '
                'it is in your inventory.')
            self.assertEqual(event['category'], 'system')
            self.assertEqual(event['event'], 'refresh_status')

        def state():
            item.refresh_from_db()
            char.refresh_from_db()
        await sync_to_async(state)()
        self.assertFalse(item.is_equipped)
        self.assertEqual(item.equipped_slot, '')
        self.assertEqual(char.outfit_snapshot, sentinel)
        vit_after, lon_after = await sync_to_async(bar_fractions)(char)
        self.assertLess(abs(vit_after - vit_before), 0.01)
        self.assertLess(abs(lon_after - lon_before), 0.01)

    async def test_cursed_comes_off_effects_untouched(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_uq2')

        def build():
            item = make_carried(
                'door_uq2', char, 'Test Clinging Band', is_equipped=True,
                equipped_slot='NECK')
            curse = make_cursed('door_uq2', char, item)
            return item, curse
        item, curse = await sync_to_async(build)()
        async with self.door(agent) as comm:
            result = await self._unequip(comm, char, item.pk)
            self.assertTrue(result['ok'],
                            'No protective guards: cursed comes off.')

        def state():
            item.refresh_from_db()
            curse.refresh_from_db()
        await sync_to_async(state)()
        self.assertFalse(item.is_equipped)
        # Unequip is not removal: the curse effects stay live.
        self.assertTrue(curse.is_active)
        self.assertEqual(curse.removed_by, '')
        self.assertTrue(item.is_cursed)

    async def test_not_equipped_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_uq3')
        item = await sync_to_async(make_carried)(
            'door_uq3', char, 'Test Pocket Band')
        async with self.door(agent) as comm:
            result = await self._unequip(comm, char, item.pk)
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-equipped')


# ----------------------------------------------------------------------
# grant_copper / deduct_copper (v25.14, #320)
# ----------------------------------------------------------------------

class DoorCopperTests(DoorTestBase):

    def _set_copper(self, char, amount):
        Character.objects.filter(pk=char.pk).update(copper=amount)

    def _get_copper(self, char):
        return Character.objects.get(pk=char.pk).copper

    async def _copper(self, char):
        return await sync_to_async(self._get_copper)(char)

    async def test_grant_happy_path_denominated(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_gc1')
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'gc1', 'act': 'grant_copper',
                'params': {'to': char.name, 'gold': 2, 'silver': 5}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {
                'granted_copper': 2050,
                'amount_display': '2 golds, 5 silvers',
                'balance_copper': 2050,
                'balance_display': '2 golds, 5 silvers'})
            self.assertEqual(await self._copper(char), 2050)

    async def test_online_grant_sends_one_reward_line_zone_local(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_gc2')

        def alias_zone():
            zone.slug = 'the-neon-sprawl'
            zone.save(update_fields=['slug'])
        await sync_to_async(alias_zone)()
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'gc2', 'act': 'grant_copper',
                'params': {'to': char.name, 'gold': 2, 'silver': 5}})
            self.assertTrue(result['ok'])
            self.assertEqual(len(layer.sent), 1)
            group, event = layer.sent[0]
            self.assertEqual(group, f'player_{char.pk}')
            self.assertEqual(event['category'], 'reward')
            self.assertEqual(
                event['text'],
                'An admin granted you 2 Megacredits, 5 Kilocredits.')
            # Result data stays engine-named regardless of zone.
            self.assertEqual(result['data']['amount_display'],
                             '2 golds, 5 silvers')

    async def test_offline_grant_sends_nothing(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_gc3')
        layer = RecordingLayer()
        async with self.door(agent, layer=layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'gc3', 'act': 'grant_copper',
                'params': {'to': char.name, 'copper': 7}})
            self.assertTrue(result['ok'])
            self.assertEqual(layer.sent, [])
            self.assertEqual(await self._copper(char), 7)

    async def test_deduct_happy_path_with_system_line(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_dc1')
        await sync_to_async(self._set_copper)(char, 2050)
        fake = FakeDoorClient()
        fake.set_online(char)
        layer = RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'dc1', 'act': 'deduct_copper',
                'params': {'to': char.name, 'gold': 1}})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {
                'deducted_copper': 1000,
                'amount_display': '1 gold',
                'balance_copper': 1050,
                'balance_display': '1 gold, 5 silvers'})
            self.assertEqual(await self._copper(char), 1050)
            self.assertEqual(len(layer.sent), 1)
            group, event = layer.sent[0]
            self.assertEqual(group, f'player_{char.pk}')
            self.assertEqual(event['category'], 'system')
            self.assertEqual(event['text'],
                             'An admin took 1 gold from you.')

    async def test_deduct_insufficient_funds_refused_exactly(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_dc2')
        await sync_to_async(self._set_copper)(char, 30)
        async with self.door(agent) as comm:
            result = await request(comm, {
                'type': 'action', 'id': 'dc2', 'act': 'deduct_copper',
                'params': {'to': char.name, 'gold': 1}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'insufficient-funds')
            self.assertIn('3 silvers', result['detail'])
            self.assertIn('1 gold', result['detail'])
            self.assertEqual(await self._copper(char), 30)

    async def test_validation_refusals_leave_balance_unchanged(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('door_gc4')
        await sync_to_async(self._set_copper)(char, 500)
        bad_amounts = [
            {},                    # no denomination at all
            {'gold': 0},           # zero
            {'silver': -3},        # negative
            {'copper': True},      # boolean
            {'copper': 'ten'},     # non-int
        ]
        async with self.door(agent) as comm:
            for i, amount in enumerate(bad_amounts):
                for act in ('grant_copper', 'deduct_copper'):
                    result = await request(comm, {
                        'type': 'action', 'id': f'v{i}{act[0]}',
                        'act': act,
                        'params': dict(amount, to=char.name)})
                    self.assertFalse(result['ok'], (act, amount))
                    self.assertEqual(result['error'], 'bad-params',
                                     (act, amount))
            result = await request(comm, {
                'type': 'action', 'id': 'vnf', 'act': 'grant_copper',
                'params': {'to': 'Nobody Such', 'gold': 1}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')
            self.assertEqual(await self._copper(char), 500)

    def test_kinds_registered(self):
        self.assertIn('grant_copper', mc_door.ACTION_HANDLERS)
        self.assertIn('deduct_copper', mc_door.ACTION_HANDLERS)


class DoorNewKindsKillSwitchTests(DoorTestBase):
    """The consumer-level gate covers the v25.7 kinds — prove it."""

    async def test_killed_switch_severs_new_query_kind_4503(self):
        agent = await sync_to_async(make_agent)('door_nk1')
        async with self.door(agent) as comm:
            await sync_to_async(engage_switch)()
            await comm.send_json_to({
                'type': 'query', 'id': '1', 'q': 'inventory',
                'params': {'name': 'anyone'}})
            message = await comm.receive_output(timeout=10)
            self.assertEqual(message['type'], 'websocket.close')
            self.assertEqual(message['code'], 4503)

    async def test_killed_switch_severs_new_action_kind_4503(self):
        agent = await sync_to_async(make_agent)('door_nk2')
        async with self.door(agent) as comm:
            await sync_to_async(engage_switch)()
            await comm.send_json_to({
                'type': 'action', 'id': '1', 'act': 'remove_item',
                'params': {'name': 'anyone', 'item_id': 1}})
            message = await comm.receive_output(timeout=10)
            self.assertEqual(message['type'], 'websocket.close')
            self.assertEqual(message['code'], 4503)
