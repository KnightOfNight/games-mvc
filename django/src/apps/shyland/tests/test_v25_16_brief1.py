"""V25.16 Brief 1 (#315): instance-side durability posture at the door.

Shape A — the door refuses ``durability_current`` edits on non-wearing
definitions entirely (every value, judged on the pre-edit posture), and
a wearing -> non-wearing posture flip on an artifact definition resets
its instance to healthy in the same atomic edit.
"""

from asgiref.sync import sync_to_async

from apps.shyland.management.commands.seed_world import WEAPON_DUR
from apps.shyland.models import ItemDefinition, ItemInstance

from .test_mc_agent_door import (
    DoorTestBase, full_weapon_spec, make_carried, request,
)


def make_nonwearing_carried(prefix, char, name):
    """One owned ordinary instance over a non-wearing definition."""
    defn = ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type='accessory', genre_tag='fantasy',
        description='Test gear that does not wear.',
        valid_slots=['NECK'], scaling_base=0.0, scaling_factor=0.0,
        base_value=1, takes_durability_loss=False, durability_table=[],
    )
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity='common')


class InstancePostureTests(DoorTestBase):

    async def _create_artifact(self, comm, char, spec, frame_id='ca'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'create_artifact',
            'params': {'to': char.name, 'spec': spec}})

    async def _edit(self, comm, char, item_id, changes, frame_id='e1'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'edit_item',
            'params': {'name': char.name, 'item_id': item_id,
                       'changes': changes}})

    async def _instance_state(self, item_id):
        item = await sync_to_async(ItemInstance.objects.get)(pk=item_id)
        return item.durability_current, item.is_broken

    async def test_shape_a_refusal_ordinary_item(self):
        # Shape A is total: 0, 50, and 100 all refuse on a non-wearing
        # definition; the instance is untouched after each.
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c1')
        item = await sync_to_async(make_nonwearing_carried)(
            'ip_c1', char, 'Test Inert Band')
        async with self.door(agent) as comm:
            for frame_id, value in (('s1', 0), ('s2', 50), ('s3', 100)):
                result = await self._edit(
                    comm, char, item.pk,
                    {'durability_current': value}, frame_id)
                self.assertFalse(result['ok'])
                self.assertEqual(result['error'], 'bad-params')
                self.assertIn('durability loss', result['detail'])
                self.assertEqual(await self._instance_state(item.pk),
                                 (100.0, False))

    async def test_whole_request_atomicity(self):
        # One refused durability key poisons the whole request (#289):
        # the mk_tier does not land.
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c2')
        item = await sync_to_async(make_nonwearing_carried)(
            'ip_c2', char, 'Test Atomic Band')
        async with self.door(agent) as comm:
            result = await self._edit(comm, char, item.pk, {
                'mk_tier': 3, 'durability_current': 0}, 'w1')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            fresh = await sync_to_async(ItemInstance.objects.get)(pk=item.pk)
            self.assertEqual(fresh.mk_tier, 1)
            self.assertEqual(fresh.durability_current, 100.0)
            self.assertFalse(fresh.is_broken)

    async def test_wearing_path_pin(self):
        # Byte-identical wearing behavior: range, is_broken coupling,
        # and the #314 integral rule all exactly as shipped.
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c3')
        item = await sync_to_async(make_carried)(
            'ip_c3', char, 'Test Wearing Band')
        async with self.door(agent) as comm:
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 40}, 'wp1')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item.pk),
                             (40.0, False))
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 0}, 'wp2')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item.pk),
                             (0.0, True))
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 55.5}, 'wp3')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('integral', result['detail'])

    async def _flipped_wearing_artifact(self, comm, char, name):
        """A wearing artifact (posture pair applied post-creation)."""
        result = await self._create_artifact(
            comm, char, full_weapon_spec(name))
        self.assertTrue(result['ok'])
        item_id = result['data']['item_id']
        result = await self._edit(comm, char, item_id, {
            'takes_durability_loss': True,
            'durability_table': WEAPON_DUR}, 'fw')
        self.assertTrue(result['ok'])
        return item_id

    async def test_flip_reset_damaged(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c4')
        async with self.door(agent) as comm:
            item_id = await self._flipped_wearing_artifact(
                comm, char, 'Test Reset Blade')
            result = await self._edit(
                comm, char, item_id, {'durability_current': 40}, 'fr1')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item_id),
                             (40.0, False))
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': False,
                'durability_table': []}, 'fr2')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item_id),
                             (100.0, False))

    async def test_flip_reset_broken(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c5')
        async with self.door(agent) as comm:
            item_id = await self._flipped_wearing_artifact(
                comm, char, 'Test Shattered Blade')
            result = await self._edit(
                comm, char, item_id, {'durability_current': 0}, 'fb1')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item_id),
                             (0.0, True))
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': False,
                'durability_table': []}, 'fb2')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item_id),
                             (100.0, False))

    async def test_combined_request_reset_wins(self):
        # Wearing artifact: durability set + flip to non-wearing in one
        # request is accepted, and the flip reset wins (the definition
        # edit runs after the instance edit).
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c6')
        async with self.door(agent) as comm:
            item_id = await self._flipped_wearing_artifact(
                comm, char, 'Test Combined Blade')
            result = await self._edit(comm, char, item_id, {
                'durability_current': 50,
                'takes_durability_loss': False,
                'durability_table': []}, 'cr1')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item_id),
                             (100.0, False))

    async def test_combined_request_pre_edit_posture_judges(self):
        # Non-wearing artifact: flip-to-wearing + durability set in one
        # request refuses (pre-edit posture judges); the two-request
        # path is the documented shape. Definition untouched after.
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c7')
        async with self.door(agent) as comm:
            result = await self._create_artifact(
                comm, char, full_weapon_spec('Test Eager Blade'))
            self.assertTrue(result['ok'])
            item_id = result['data']['item_id']
            defn_id = result['data']['definition_id']
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR,
                'durability_current': 50}, 'pj1')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('durability loss', result['detail'])
            defn = await sync_to_async(ItemDefinition.objects.get)(
                pk=defn_id)
            self.assertFalse(defn.takes_durability_loss)
            self.assertEqual(defn.durability_table, [])
            self.assertEqual(await self._instance_state(item_id),
                             (100.0, False))

    async def test_idempotent_reassert_heals_stranded(self):
        # A pre-25.16 stranded instance (hand-set via ORM, the shape
        # the 0057 migration also heals): re-asserting the non-wearing
        # posture resets it.
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('ip_c8')
        async with self.door(agent) as comm:
            result = await self._create_artifact(
                comm, char, full_weapon_spec('Test Stranded Blade'))
            self.assertTrue(result['ok'])
            item_id = result['data']['item_id']
            await sync_to_async(
                ItemInstance.objects.filter(pk=item_id).update)(
                durability_current=0.0, is_broken=True)
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': False,
                'durability_table': []}, 'ir1')
            self.assertTrue(result['ok'])
            self.assertEqual(await self._instance_state(item_id),
                             (100.0, False))
