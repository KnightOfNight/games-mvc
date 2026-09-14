"""V26.1 Brief 1 — Longevity First Drain (#70).

The flee fuel gate (ceil(max/4) charged on every contested attempt —
success, failure, nowhere-to-run alike; free refusal below the cost with
no cooldown; exactly-at fires to 0; out-of-combat and empty-session
paths exempt), the regen regime rule (interval form below
LONGEVITY_REGEN_SECS, vitality-shaped per-tick form at or above it), the
percent_restore_amount generalization with percent_heal_amount as a thin
delegate, the restore_longevity_percent instant branch (Draught-Law
shape: fraction of MAX, 25-point floor, math.ceil), the potion's
stop-at-full mirror, and the Stamina Potion's seeded wiring.
"""

import asyncio
import io
import math
from unittest import mock

from asgiref.sync import sync_to_async

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from apps.shyland.effect_utils import (
    apply_effect_definition, percent_heal_amount, percent_restore_amount,
)
from apps.shyland.models import (
    Character, EffectComponent, EffectDefinition, ItemDefinition,
    ItemInstance, LONGEVITY_PERCENT_RESTORE_FLOOR, LONGEVITY_REGEN_SECS,
    VendorEntry,
)

from .test_combat_state import (
    make_character as make_combat_character,
    make_npc, make_npc_definition,
    make_world as make_combat_world,
)
from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world, outputs,
)
from .test_mc_sink import EmitRecorder
from .test_v243_regen import get_bars, run_regen_engine, set_bars
from .test_zombie_sessions import make_session


def statuses(sent):
    return [m for m in sent if m.get('type') == 'status']


def longevity(char):
    c = Character.objects.get(pk=char.pk)
    return c.longevity_current, c.longevity_max


def make_potion_effect(prefix):
    """The seeded potion's exact shape: restore_longevity_percent,
    0.15 + 0.05×Mk fraction of longevity_max, instantaneous."""
    potion = EffectDefinition.objects.create(
        name=f'{prefix} Stamina', slug=f'{prefix}-stamina')
    EffectComponent.objects.create(
        definition=potion, component_type='restore_longevity_percent',
        magnitude_base=0.15, magnitude_scaling=0.05,
        duration_base=0.0, duration_scaling=0.0,
    )
    return potion


def setup_potions(prefix, count=1, longevity=(50, 100)):
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    current, maximum = longevity
    Character.objects.filter(pk=char.pk).update(
        longevity_current=current, longevity_max=maximum)
    char.longevity_current, char.longevity_max = current, maximum
    effect = make_potion_effect(prefix)
    potion_def = make_item_def(prefix, 'Stamina Potion', 'consumable',
                               effect=effect)
    for _ in range(count):
        make_owned_item(potion_def, char)
    return char, potion_def


class FleeFuelGateTests(TransactionTestCase):
    """#70: the contested flee costs ceil(longevity_max / 4); refusal
    below the cost is free (no deduction, no cooldown); exactly-at fires
    and lands at 0; the exempt paths never see the gate."""

    def _combat_setup(self, prefix, lon_current, lon_max=200,
                      npc_per=1, with_exit=False):
        zone, room = make_combat_world(prefix)
        char = make_combat_character(prefix, room)
        Character.objects.filter(pk=char.pk).update(
            longevity_current=lon_current, longevity_max=lon_max)
        char.refresh_from_db()
        definition = make_npc_definition(prefix)
        if npc_per != 1:
            definition.base_per = npc_per
            definition.save(update_fields=['base_per'])
        npc = make_npc(definition, room, hp=50)
        session = make_session(char, [npc], room)
        if with_exit:
            refuge = zone.rooms.create(
                name=f'{prefix} Refuge', description='Long.',
                brief_description='Brief.', coord_x=0, coord_y=1)
            room.exit_north = refuge
            room.save(update_fields=['exit_north'])
        return char, session, room

    def test_contested_success_deducts_exactly_the_cost(self):
        char, session, room = self._combat_setup(
            'ffA', 200, npc_per=1, with_exit=True)
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer.last_direction = None
        with mock.patch('apps.shyland.mc.mc_emit', new=EmitRecorder()), \
             mock.patch('apps.shyland.consumers.random.randint',
                        return_value=20):
            asyncio.run(consumer.cmd_flee())
        lon, lon_max = longevity(char)
        self.assertEqual(lon, 200 - math.ceil(200 / 4))
        self.assertEqual(lon, 150)

    def test_contested_failure_deducts_and_refreshes_status(self):
        char, session, room = self._combat_setup('ffB', 200, npc_per=500)
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer.last_direction = None
        with mock.patch('apps.shyland.mc.mc_emit', new=EmitRecorder()), \
             mock.patch('apps.shyland.consumers.random.randint',
                        return_value=1):
            asyncio.run(consumer.cmd_flee())
        lon, _ = longevity(char)
        self.assertEqual(lon, 150)
        # The attempt was purchased: the cooldown recorded, the fight on.
        session.refresh_from_db()
        self.assertIsNotNone(session.last_flee_attempt_at)
        self.assertTrue(session.is_active)
        # The pane shows the spent fuel — a status refresh went out.
        self.assertTrue(statuses(sent))

    def test_refusal_below_cost_is_free(self):
        char, session, room = self._combat_setup('ffC', 49, npc_per=500)
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer.last_direction = None
        with mock.patch('apps.shyland.mc.mc_emit', new=EmitRecorder()):
            asyncio.run(consumer.cmd_flee())
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'You are too spent to flee!')
        self.assertEqual(msgs[0]['category'], 'warn')
        # Free: no deduction, no cooldown, no status refresh.
        lon, _ = longevity(char)
        self.assertEqual(lon, 49)
        session.refresh_from_db()
        self.assertIsNone(session.last_flee_attempt_at)
        self.assertTrue(session.is_active)
        self.assertFalse(statuses(sent))

    def test_exactly_at_cost_fires_and_lands_at_zero(self):
        char, session, room = self._combat_setup('ffD', 50, npc_per=500)
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer.last_direction = None
        with mock.patch('apps.shyland.mc.mc_emit', new=EmitRecorder()), \
             mock.patch('apps.shyland.consumers.random.randint',
                        return_value=1):
            asyncio.run(consumer.cmd_flee())
        # The contest ran (failure outcome) and the fuel hit exactly 0.
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn(
            'You tried to flee but your enemies are too strong.', texts)
        lon, _ = longevity(char)
        self.assertEqual(lon, 0)

    def test_empty_session_disengage_is_exempt(self):
        zone, room = make_combat_world('ffE')
        char = make_combat_character('ffE', room)
        # Below the would-be cost — the exempt path must not gate on it.
        Character.objects.filter(pk=char.pk).update(
            longevity_current=10, longevity_max=200)
        char.refresh_from_db()
        session = make_session(char, [], room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer.last_direction = None
        with mock.patch('apps.shyland.mc.mc_emit', new=EmitRecorder()):
            asyncio.run(consumer.cmd_flee())
        session.refresh_from_db()
        self.assertFalse(session.is_active)
        lon, _ = longevity(char)
        self.assertEqual(lon, 10)

    def test_out_of_combat_flee_is_byte_unchanged(self):
        zone, room = make_combat_world('ffF')
        char = make_combat_character('ffF', room)
        Character.objects.filter(pk=char.pk).update(
            longevity_current=10, longevity_max=200)
        char.refresh_from_db()
        sent = []
        consumer = make_stub_consumer(char, sent)
        with mock.patch('apps.shyland.mc.mc_emit', new=EmitRecorder()):
            asyncio.run(consumer.cmd_flee())
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'You are not in combat.')
        self.assertEqual(msgs[0]['category'], 'warn')
        lon, _ = longevity(char)
        self.assertEqual(lon, 10)


class RegenRegimeTests(TransactionTestCase):
    """#70: the regime rule — interval form below LONGEVITY_REGEN_SECS
    (as shipped), Vitality's per-tick shape at or above it."""

    async def test_interval_form_below_the_constant(self):
        def setup():
            zone, room = make_world('rgA')
            char = make_character('rgA', room)
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=274, longevity_current=100)
            return char
        char = await sync_to_async(setup)()

        interval = math.ceil(LONGEVITY_REGEN_SECS / 274)
        self.assertEqual(interval, 4)

        cmd, sent = run_regen_engine()
        await cmd.process_effects(interval * 2)      # 8 % 4 == 0 — fires
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 101)

        await cmd.process_effects(interval * 2 + 1)  # adjacent tick
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 101)                   # nothing this tick

    async def test_per_tick_form_at_the_constant_boundary(self):
        def setup():
            zone, room = make_world('rgB')
            char = make_character('rgB', room)
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=LONGEVITY_REGEN_SECS,
                     longevity_current=100)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        # ceil(900 / 900) = 1 per tick — on EVERY tick, no interval.
        await cmd.process_effects(7)                 # 7 % anything — fires
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 101)
        await cmd.process_effects(8)
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 102)

    async def test_per_tick_form_above_the_constant(self):
        def setup():
            zone, room = make_world('rgC')
            char = make_character('rgC', room)
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=1800, longevity_current=100)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(7)
        vit, lon = await sync_to_async(get_bars)(char)
        # ceil(1800 / 900) = 2 points per tick, regardless of deficit.
        self.assertEqual(lon, 102)

    async def test_per_tick_form_clamps_at_max(self):
        def setup():
            zone, room = make_world('rgD')
            char = make_character('rgD', room)
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=1800, longevity_current=1799)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(7)
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 1800)   # +2, clamped — never overshoots

    async def test_interval_form_clamps_at_max(self):
        def setup():
            zone, room = make_world('rgE')
            char = make_character('rgE', room)
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=274, longevity_current=274)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(4)                 # an interval tick
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 274)


class PercentRestoreAmountTests(SimpleTestCase):
    """#70: the generalized Draught-Law arithmetic and the delegation."""

    def test_ceil_never_round(self):
        # ceil(0.15 × 274) = ceil(41.1) = 42 — round() would give 41.
        self.assertEqual(percent_restore_amount(0.15, 274, 25), 42)

    def test_fraction_of_max(self):
        self.assertEqual(percent_restore_amount(0.20, 274, 25), 55)

    def test_the_floor_governs_small_bars(self):
        # ceil(0.20 × 100) = 20 < 25 — the floor wins.
        self.assertEqual(percent_restore_amount(0.20, 100, 25), 25)
        self.assertEqual(LONGEVITY_PERCENT_RESTORE_FLOOR, 25)

    def test_percent_heal_amount_delegates_unchanged(self):
        # Spot-check existing vitality values: the v24.3-era anchors.
        self.assertEqual(percent_heal_amount(0.20, 718), 144)
        self.assertEqual(percent_heal_amount(0.20, 100), 25)   # floor
        self.assertEqual(percent_heal_amount(0.20, 718),
                         percent_restore_amount(0.20, 718, 25))


class RestoreLongevityPercentApplyTests(TestCase):
    """#70: the instant branch — fraction of longevity_max, floored,
    atomic, clamped; the annotation carries the actual amount."""

    def _char(self, prefix, current, maximum):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        Character.objects.filter(pk=char.pk).update(
            longevity_current=current, longevity_max=maximum)
        char.refresh_from_db()
        return char

    def test_mk1_restores_fraction_of_max(self):
        char = self._char('rlA', 100, 274)
        effect = make_potion_effect('rlA')
        pairs = apply_effect_definition(effect, char, 1)
        # Mk 1: 0.15 + 0.05×1 = 0.20 of max — ceil(54.8) = 55.
        self.assertEqual(pairs, [('feel your stamina return',
                                  '(+55 Longevity)')])
        lon, _ = longevity(char)
        self.assertEqual(lon, 155)

    def test_floor_governs_the_default_bar(self):
        char = self._char('rlB', 50, 100)
        effect = make_potion_effect('rlB')
        pairs = apply_effect_definition(effect, char, 1)
        # ceil(0.20 × 100) = 20 < 25: the floor governs (the deliberate
        # Mk-1 shortfall against flee's 25% cost).
        self.assertEqual(pairs, [('feel your stamina return',
                                  '(+25 Longevity)')])
        lon, _ = longevity(char)
        self.assertEqual(lon, 75)

    def test_clamps_at_max(self):
        char = self._char('rlC', 90, 100)
        effect = make_potion_effect('rlC')
        apply_effect_definition(effect, char, 1)
        lon, _ = longevity(char)
        self.assertEqual(lon, 100)


class StopAtFullTests(TransactionTestCase):
    """#70: the potion's stop-at-full mirror — refusal at full Longevity
    consumes nothing; at a deficit it applies and consumes."""

    async def test_full_longevity_refuses_and_keeps_the_item(self):
        char, potion_def = await sync_to_async(setup_potions)(
            'sfA', count=1, longevity=(100, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('stamina potion')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'You are already at full stamina.')
        self.assertEqual(msgs[0]['category'], 'warn')
        count = await sync_to_async(
            lambda: ItemInstance.objects.filter(owner=char).count())()
        self.assertEqual(count, 1)
        lon, _ = await sync_to_async(longevity)(char)
        self.assertEqual(lon, 100)

    async def test_deficit_applies_and_consumes(self):
        char, potion_def = await sync_to_async(setup_potions)(
            'sfB', count=1, longevity=(50, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('stamina potion')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Stamina Potion Mk 1 and feel your stamina return. '
            '(+25 Longevity)')
        self.assertEqual(msgs[0]['category'], 'success')
        count = await sync_to_async(
            lambda: ItemInstance.objects.filter(owner=char).count())()
        self.assertEqual(count, 0)
        lon, _ = await sync_to_async(longevity)(char)
        self.assertEqual(lon, 75)


class SeedTests(TestCase):
    """#70: the Stamina Potion's seeded wiring — definition, effect,
    component, value, and the five vendors at 15 cp."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_world', stdout=io.StringIO())

    def test_potion_definition_and_effect_wiring(self):
        defn = ItemDefinition.objects.get(slug='stamina-potion')
        self.assertEqual(defn.name, 'Stamina Potion')
        self.assertEqual(defn.item_type, 'consumable')
        self.assertEqual(defn.base_value, 15)
        self.assertFalse(defn.takes_durability_loss)
        effect = defn.effect
        self.assertEqual(effect.slug, 'stamina-potion')
        components = list(effect.components.all())
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component.component_type,
                         'restore_longevity_percent')
        self.assertEqual(component.magnitude_base, 0.15)
        self.assertEqual(component.magnitude_scaling, 0.05)
        self.assertEqual(component.duration_base, 0.0)
        self.assertEqual(component.duration_scaling, 0.0)
        self.assertTrue(component.is_instantaneous())

    def test_all_five_vendors_list_the_potion_at_15(self):
        entries = VendorEntry.objects.filter(
            item_definition__slug='stamina-potion')
        vendors = {e.npc_definition.slug for e in entries}
        # Three authored + the two Convergence carts' automatic pickup.
        self.assertEqual(vendors, {
            'essa-the-trader', 'sona-the-trader', 'ridda-the-trader',
            'vnd-9', 'mother-tansy',
        })
        self.assertTrue(all(e.price == 15 for e in entries))

    def test_no_loot_table_entries(self):
        from apps.shyland.models import LootTableEntry
        self.assertFalse(LootTableEntry.objects.filter(
            item_definition__slug='stamina-potion').exists())
