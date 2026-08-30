"""V25.12 Brief 1 (#311, #312, #314): the durability-posture invariant.

One shared validator behind three enforcement layers — model clean()
(the admin form), the agent door's edit path, and the DB CheckConstraint
on the cheap core — plus the door's artifacts-don't-wear creation
posture and the #314 integral-durability rule on instance edits.
"""

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.forms import BooleanField, modelform_factory
from django.test import SimpleTestCase, TestCase

from apps.shyland.management.commands.seed_world import WEAPON_DUR
from apps.shyland.models import (
    ItemDefinition, ItemInstance, durability_posture_violations,
)

from .test_mc_agent_door import (
    DoorTestBase, full_weapon_spec, make_carried, request,
)

FULL_TABLE = [{'min': 0, 'max': 100, 'penalty': 0.0}]
GAPPY_TABLE = [{'min': 0, 'max': 40, 'penalty': 0.0},
               {'min': 60, 'max': 100, 'penalty': 0.0}]


def build_definition(**overrides):
    """An unsaved, fully-populated definition in the legal non-wearing
    posture; overrides push it wherever a test needs it."""
    fields = dict(
        name='Posture Probe', slug='posture-probe', item_type='consumable',
        genre_tag='fantasy', description='A definition built to probe '
        'the durability-posture invariant.',
        scaling_base=0.0, scaling_factor=0.0,
        takes_durability_loss=False, durability_table=[],
    )
    fields.update(overrides)
    return ItemDefinition(**fields)


# ----------------------------------------------------------------------
# The shared validator (§3.2/§3.3 rules)
# ----------------------------------------------------------------------

class ValidatorTests(SimpleTestCase):

    def test_wear_on_empty_table_fails(self):
        violations = durability_posture_violations(True, [])
        self.assertEqual(len(violations), 1)
        self.assertIn('non-empty', violations[0])

    def test_gappy_table_fails_naming_the_gap(self):
        violations = durability_posture_violations(True, GAPPY_TABLE)
        self.assertEqual(len(violations), 1)
        self.assertIn('41-59', violations[0])

    def test_missing_key_fails(self):
        violations = durability_posture_violations(
            True, [{'min': 0, 'max': 100}])
        self.assertTrue(any('exactly the keys' in v for v in violations))

    def test_extra_key_fails(self):
        violations = durability_posture_violations(
            True, [{'min': 0, 'max': 100, 'penalty': 0.0, 'bonus': 1}])
        self.assertTrue(any('exactly the keys' in v for v in violations))

    def test_min_over_max_fails(self):
        violations = durability_posture_violations(
            True, [{'min': 50, 'max': 40, 'penalty': 0.0}])
        self.assertTrue(any('0 <= min <= max <= 100' in v
                            for v in violations))

    def test_out_of_range_bounds_fail(self):
        violations = durability_posture_violations(
            True, [{'min': 0, 'max': 150, 'penalty': 0.0}])
        self.assertTrue(any('0 <= min <= max <= 100' in v
                            for v in violations))

    def test_boolean_is_not_a_number(self):
        violations = durability_posture_violations(
            True, [{'min': True, 'max': 100, 'penalty': 0.0}])
        self.assertTrue(any("'min' must be a number" in v
                            for v in violations))

    def test_non_dict_entry_fails(self):
        violations = durability_posture_violations(True, [42])
        self.assertTrue(any('must be an object' in v for v in violations))

    def test_penalty_out_of_range_fails(self):
        violations = durability_posture_violations(
            True, [{'min': 0, 'max': 100, 'penalty': 1.5}])
        self.assertTrue(any("'penalty' must be between" in v
                            for v in violations))

    def test_weapon_dur_passes_verbatim(self):
        # Touching boundaries are legal — coverage, not non-overlap.
        self.assertEqual(durability_posture_violations(True, WEAPON_DUR),
                         [])

    def test_wear_off_nonempty_fails(self):
        violations = durability_posture_violations(False, FULL_TABLE)
        self.assertEqual(len(violations), 1)
        self.assertIn('must be empty', violations[0])

    def test_wear_off_empty_passes(self):
        self.assertEqual(durability_posture_violations(False, []), [])


# ----------------------------------------------------------------------
# clean() — the admin-form layer
# ----------------------------------------------------------------------

class CleanTests(TestCase):

    def assert_clean_refuses(self, **overrides):
        defn = build_definition(**overrides)
        with self.assertRaises(ValidationError) as caught:
            defn.full_clean()
        self.assertIn('durability_table', caught.exception.message_dict)

    def test_wear_on_empty_table_refused(self):
        self.assert_clean_refuses(takes_durability_loss=True,
                                  durability_table=[])

    def test_wear_on_gappy_table_refused(self):
        self.assert_clean_refuses(takes_durability_loss=True,
                                  durability_table=GAPPY_TABLE)

    def test_wear_off_nonempty_refused(self):
        self.assert_clean_refuses(takes_durability_loss=False,
                                  durability_table=FULL_TABLE)

    def test_both_legal_postures_pass(self):
        build_definition().full_clean()
        build_definition(takes_durability_loss=True,
                         durability_table=WEAPON_DUR).full_clean()


# ----------------------------------------------------------------------
# The DB constraint — the cheap core
# ----------------------------------------------------------------------

class ConstraintTests(TestCase):

    def test_wear_on_empty_table_create_raises(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ItemDefinition.objects.create(
                name='Constraint Probe', slug='constraint-probe',
                item_type='consumable', genre_tag='fantasy',
                description='A row the constraint must refuse.',
                scaling_base=0.0, scaling_factor=0.0,
                takes_durability_loss=True, durability_table=[],
            )
        # Rolled back: nothing landed.
        self.assertFalse(ItemDefinition.objects.filter(
            slug='constraint-probe').exists())


# ----------------------------------------------------------------------
# The door: artifacts don't wear (§3.1), posture-coupled edits (§4c),
# and the integral rule (#314, §4d)
# ----------------------------------------------------------------------

class DoorPostureTests(DoorTestBase):

    async def _create_artifact(self, comm, char, spec, frame_id='ca'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'create_artifact',
            'params': {'to': char.name, 'spec': spec}})

    async def _edit(self, comm, char, item_id, changes, frame_id='e1'):
        return await request(comm, {
            'type': 'action', 'id': frame_id, 'act': 'edit_item',
            'params': {'name': char.name, 'item_id': item_id,
                       'changes': changes}})

    async def test_created_artifact_reads_non_wearing(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('dur_c1')
        async with self.door(agent) as comm:
            result = await self._create_artifact(
                comm, char, full_weapon_spec('Test Wearless Blade'))
            self.assertTrue(result['ok'])
            defn = await sync_to_async(ItemDefinition.objects.get)(
                pk=result['data']['definition_id'])
            self.assertFalse(defn.takes_durability_loss)
            self.assertEqual(defn.durability_table, [])

    async def test_definition_edit_postures(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('dur_c2')
        async with self.door(agent) as comm:
            result = await self._create_artifact(
                comm, char, full_weapon_spec('Test Posture Blade'))
            self.assertTrue(result['ok'])
            item_id = result['data']['item_id']
            defn_id = result['data']['definition_id']
            # Wear on + a full seed-shaped table: accepted.
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': True,
                'durability_table': WEAPON_DUR}, 'p1')
            self.assertTrue(result['ok'])
            defn = await sync_to_async(ItemDefinition.objects.get)(
                pk=defn_id)
            self.assertTrue(defn.takes_durability_loss)
            self.assertEqual(defn.durability_table, WEAPON_DUR)
            # Wear on + empty: refused, naming the rule.
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': True,
                'durability_table': []}, 'p2')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('non-empty', result['detail'])
            # Wear on + gappy: refused.
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': True,
                'durability_table': GAPPY_TABLE}, 'p3')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            # Wear off + non-empty (table stays from p1): refused.
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': False}, 'p4')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('must be empty', result['detail'])
            # Both back to non-wearing together: accepted.
            result = await self._edit(comm, char, item_id, {
                'takes_durability_loss': False,
                'durability_table': []}, 'p5')
            self.assertTrue(result['ok'])

    async def test_mixed_request_refuses_whole(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('dur_c3')
        async with self.door(agent) as comm:
            result = await self._create_artifact(
                comm, char, full_weapon_spec('Test Atomic Blade'))
            self.assertTrue(result['ok'])
            item_id = result['data']['item_id']
            # One bad durability key poisons the whole request (#289
            # whole-request semantics): the mk_tier does not land.
            result = await self._edit(comm, char, item_id, {
                'mk_tier': 9, 'takes_durability_loss': True}, 'm1')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            item = await sync_to_async(ItemInstance.objects.get)(pk=item_id)
            self.assertEqual(item.mk_tier, 3)

    async def test_durability_type_rules(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('dur_c4')
        item = await sync_to_async(make_carried)(
            'dur_c4', char, 'Test Integral Band')
        async with self.door(agent) as comm:
            # takes_durability_loss must be a boolean.
            result = await self._edit(comm, char, item.pk, {
                'takes_durability_loss': 1}, 't1')
            self.assertFalse(result['ok'])
            # (not-artifact fires first on the shared template — the
            # boolean rule is exercised on an artifact below.)
            self.assertEqual(result['error'], 'not-artifact')
            result = await self._create_artifact(
                comm, char, full_weapon_spec('Test Typed Blade'), 't2')
            artifact_id = result['data']['item_id']
            result = await self._edit(comm, char, artifact_id, {
                'takes_durability_loss': 1}, 't3')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('boolean', result['detail'])
            result = await self._edit(comm, char, artifact_id, {
                'durability_table': 'nope'}, 't4')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('list', result['detail'])

    async def test_instance_durability_integral_rule(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('dur_c5')
        item = await sync_to_async(make_carried)(
            'dur_c5', char, 'Test Wholes Band')
        async with self.door(agent) as comm:
            # Integer: accepted.
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 42}, 'i1')
            self.assertTrue(result['ok'])
            await sync_to_async(item.refresh_from_db)()
            self.assertEqual(item.durability_current, 42.0)
            # Integral float (JSON clients may deliver 42.0): accepted.
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 42.0}, 'i2')
            self.assertTrue(result['ok'])
            # Fractional: refused, naming the integral rule.
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 55.5}, 'i3')
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('integral', result['detail'])
            # Zero: accepted, and the is_broken invariant holds.
            result = await self._edit(
                comm, char, item.pk, {'durability_current': 0}, 'i4')
            self.assertTrue(result['ok'])
            await sync_to_async(item.refresh_from_db)()
            self.assertEqual(item.durability_current, 0.0)
            self.assertTrue(item.is_broken)
            # The existing bool/range refusals are unchanged.
            for frame_id, value in (('i5', True), ('i6', 101)):
                result = await self._edit(
                    comm, char, item.pk,
                    {'durability_current': value}, frame_id)
                self.assertFalse(result['ok'])
                self.assertEqual(result['error'], 'bad-params')


# ----------------------------------------------------------------------
# The admin re-save gap (#312)
# ----------------------------------------------------------------------

class AdminResaveTests(TestCase):

    def test_non_wearing_definition_resaves_with_no_changes(self):
        defn = build_definition()
        defn.save()
        form_cls = modelform_factory(ItemDefinition, fields='__all__')
        unbound = form_cls(instance=defn)
        data = {}
        for name, field in unbound.fields.items():
            value = unbound.get_initial_for_field(field, name)
            if value is None:
                continue
            if isinstance(field, BooleanField) and not value:
                continue  # an unchecked checkbox posts nothing
            data[name] = field.prepare_value(value)
        form = form_cls(data=data, instance=defn)
        self.assertTrue(form.is_valid(), form.errors)

    def test_instance_with_empty_rolled_lists_cleans(self):
        defn = build_definition()
        defn.save()
        inst = ItemInstance(definition=defn, mk_tier=1, rarity='common',
                            rolled_primary_stats=[],
                            rolled_secondary_stats=[])
        inst.full_clean()
