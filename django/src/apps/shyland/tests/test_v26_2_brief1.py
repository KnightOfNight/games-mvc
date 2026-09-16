"""v26.2 Brief 1 (#330/#331): the curse engine.

Coverage per the brief's §12: the six-lane admission gate (strict-greater
admits, equal refused, duration-blind, per-lane isolation, ungated
families, join-not-replace, same-definition semantics, whole-effect
atomicity), refusal surfacing (use path kept-plus-warn, NPC path silent
skip), the #331 staleness fix (cumulative same-lane deltas, apply order,
actual-delta announcements), the generation-time latent roll (dormant
natural path, force path, rarity gate), the trap (equip springs once,
theater order, independent same-curse items), the six component types
(stat cut exact reversal, bar cuts under the bar law, multiplicative
combat factors, the floor hold's drain/arrival/silence/heal-ceiling),
lifecycle (expiry cleans, memorial, sudo teardown), and death semantics
(curse-death attribution, other-cause persistence, refill to cut max).

Engine test characters sit in an active CombatSession where regen or
drift would otherwise move the bars (the v26.0 pattern).
"""

from datetime import timedelta
from unittest import mock

from asgiref.sync import sync_to_async

from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.combat_utils import (
    apply_npc_effects_detailed, curse_combat_reads, rescale_bars_for_gear,
)
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.curse_utils import end_curse, spring_curse
from apps.shyland.effect_utils import (
    EffectRefused, _create_effect_instance, apply_effect_definition,
    apply_stat_effect, vitality_hold_value,
)
from apps.shyland.item_utils import generate_item_instance, get_display_description
from apps.shyland.models import (
    Character, CombatSession, CurseCandidate, DYING_DURATION_SECS,
    EffectComponent, EffectComponentInstance, EffectDefinition,
    EffectInstance, ItemDefinition, ItemInstance, NpcEffect,
)

from .test_combat_state import make_npc, make_npc_definition
from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world, outputs,
)
from .test_tick_expiry import run_effects_engine
from .test_zombie_sessions import make_engine, make_session

# The consumer's trap guard, unwrapped (the get_live_npcs_in_room pattern).
spring_if_latent = SkylandConsumer.__dict__['spring_curse_if_latent'].func
unequip_blocked = SkylandConsumer.__dict__['_unequip_blocked_reason']


def make_effect(prefix, components, is_curse=False, apply_text='',
                memorial_text=''):
    """EffectDefinition + real EffectComponents. Each component spec:
    ctype, magnitude (+ optional scaling/duration/target_stat/mag2/
    mag2_scale/no_expiry)."""
    definition = EffectDefinition.objects.create(
        name=f'{prefix} Effect', slug=f'{prefix}-effect',
        is_curse=is_curse, apply_text=apply_text,
        memorial_text=memorial_text,
    )
    for order, spec in enumerate(components):
        EffectComponent.objects.create(
            definition=definition,
            component_type=spec['ctype'],
            target_stat=spec.get('target_stat', ''),
            magnitude_base=spec['magnitude'],
            magnitude_scaling=spec.get('scaling', 0.0),
            duration_base=spec.get('duration', 60.0),
            duration_scaling=0.0,
            magnitude2_base=spec.get('mag2'),
            magnitude2_scaling=spec.get('mag2_scale'),
            no_expiry=spec.get('no_expiry', False),
            order=order,
        )
    return definition


def make_latent_item(prefix, char, curse, rarity='rare'):
    """An owned, identified item carrying an unsprung latent curse."""
    defn = ItemDefinition.objects.create(
        name=f'{prefix} Mace', slug=f'{prefix}-mace', item_type='weapon',
        genre_tag='fantasy', valid_slots=['MAIN_HAND'],
        scaling_base=0.0, scaling_factor=0.0,
        takes_durability_loss=False, durability_table=[],
    )
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity=rarity,
        durability_current=100.0, is_identified=True,
        is_cursed=True, latent_curse=curse,
    )


def set_bars(char, **kwargs):
    Character.objects.filter(pk=char.pk).update(**kwargs)
    char.refresh_from_db()


def enter_combat(char, room):
    session = CombatSession.objects.create(room=room, is_active=True)
    session.characters.add(char)
    return session


def active_instances(char):
    return list(EffectInstance.objects.filter(target=char, is_active=True))


# ----------------------------------------------------------------------
# §12.1 — the admission gate
# ----------------------------------------------------------------------

class AdmissionGateTests(TestCase):

    def _world(self, prefix):
        zone, room = make_world(prefix)
        return make_character(prefix, room)

    def test_strict_greater_admits_hot_and_dot(self):
        char = self._world('admA')
        apply_effect_definition(
            make_effect('admA-w', [{'ctype': 'hot_vitality', 'magnitude': 3.0}]),
            char, 1)
        apply_effect_definition(
            make_effect('admA-s', [{'ctype': 'hot_vitality', 'magnitude': 6.0}]),
            char, 1)
        apply_effect_definition(
            make_effect('admA-wd', [{'ctype': 'dot_vitality', 'magnitude': 2.0}]),
            char, 1)
        apply_effect_definition(
            make_effect('admA-sd', [{'ctype': 'dot_vitality', 'magnitude': 5.0}]),
            char, 1)
        self.assertEqual(len(active_instances(char)), 4)

    def test_equal_refused_both_lanes(self):
        char = self._world('admB')
        apply_effect_definition(
            make_effect('admB-1', [{'ctype': 'hot_vitality', 'magnitude': 3.0}]),
            char, 1)
        with self.assertRaises(EffectRefused) as ctx:
            apply_effect_definition(
                make_effect('admB-2', [{'ctype': 'hot_vitality', 'magnitude': 3.0}]),
                char, 1)
        self.assertEqual(ctx.exception.blocking_name, 'admB-1 Effect')
        apply_effect_definition(
            make_effect('admB-3', [{'ctype': 'dot_longevity', 'magnitude': 4.0}]),
            char, 1)
        with self.assertRaises(EffectRefused):
            apply_effect_definition(
                make_effect('admB-4', [{'ctype': 'dot_longevity', 'magnitude': 4.0}]),
                char, 1)

    def test_weaker_refused_and_kept_none_applied(self):
        char = self._world('admC')
        apply_effect_definition(
            make_effect('admC-s', [{'ctype': 'hot_vitality', 'magnitude': 6.0}]),
            char, 1)
        before = len(active_instances(char))
        with self.assertRaises(EffectRefused):
            apply_effect_definition(
                make_effect('admC-w', [{'ctype': 'hot_vitality', 'magnitude': 3.0}]),
                char, 1)
        self.assertEqual(len(active_instances(char)), before)

    def test_duration_plays_no_role(self):
        char = self._world('admD')
        apply_effect_definition(
            make_effect('admD-long',
                        [{'ctype': 'hot_vitality', 'magnitude': 5.0,
                          'duration': 3600.0}]),
            char, 1)
        # Shorter but stronger admits.
        apply_effect_definition(
            make_effect('admD-short',
                        [{'ctype': 'hot_vitality', 'magnitude': 6.0,
                          'duration': 5.0}]),
            char, 1)
        self.assertEqual(len(active_instances(char)), 2)

    def test_per_lane_isolation(self):
        char = self._world('admE')
        apply_effect_definition(
            make_effect('admE-dot', [{'ctype': 'dot_vitality', 'magnitude': 50.0}]),
            char, 1)
        # A dot never gates a hot; bars never cross.
        apply_effect_definition(
            make_effect('admE-hot', [{'ctype': 'hot_vitality', 'magnitude': 1.0}]),
            char, 1)
        apply_effect_definition(
            make_effect('admE-lon', [{'ctype': 'hot_longevity', 'magnitude': 1.0}]),
            char, 1)
        self.assertEqual(len(active_instances(char)), 3)

    def test_shifts_and_stats_ungated(self):
        char = self._world('admF')
        apply_effect_definition(
            make_effect('admF-1', [{'ctype': 'shift_acuity_high', 'magnitude': 0.5}]),
            char, 1)
        apply_effect_definition(
            make_effect('admF-2', [{'ctype': 'shift_acuity_high', 'magnitude': 0.1}]),
            char, 1)
        apply_effect_definition(
            make_effect('admF-3', [{'ctype': 'stat_bonus', 'magnitude': 5.0,
                                    'target_stat': 'str'}]),
            char, 1)
        apply_effect_definition(
            make_effect('admF-4', [{'ctype': 'stat_bonus', 'magnitude': 1.0,
                                    'target_stat': 'str'}]),
            char, 1)
        self.assertEqual(len(active_instances(char)), 4)

    def test_admission_joins_never_replaces(self):
        char = self._world('admG')
        weak = make_effect('admG-w', [{'ctype': 'hot_vitality', 'magnitude': 3.0}])
        apply_effect_definition(weak, char, 1)
        apply_effect_definition(
            make_effect('admG-s', [{'ctype': 'hot_vitality', 'magnitude': 6.0}]),
            char, 1)
        weak_instance = EffectInstance.objects.get(definition=weak, target=char)
        self.assertTrue(weak_instance.is_active)

    def test_same_definition_higher_mk_refreshes(self):
        char = self._world('admH')
        definition = make_effect(
            'admH', [{'ctype': 'hot_vitality', 'magnitude': 3.0, 'scaling': 1.0}])
        apply_effect_definition(definition, char, 1)
        apply_effect_definition(definition, char, 2)
        rows = EffectInstance.objects.filter(
            definition=definition, target=char).order_by('pk')
        self.assertFalse(rows[0].is_active)
        self.assertEqual(rows[0].removed_by, 'reapplication')
        self.assertTrue(rows[1].is_active)
        self.assertEqual(rows[1].mk_tier, 2)

    def test_same_definition_lower_mk_raises(self):
        char = self._world('admI')
        definition = make_effect(
            'admI', [{'ctype': 'hot_vitality', 'magnitude': 3.0, 'scaling': 1.0}])
        apply_effect_definition(definition, char, 2)
        with self.assertRaises(EffectRefused) as ctx:
            apply_effect_definition(definition, char, 1)
        self.assertEqual(ctx.exception.blocking_name, 'admI Effect')

    def test_whole_effect_atomicity(self):
        char = self._world('admJ')
        apply_effect_definition(
            make_effect('admJ-inc', [{'ctype': 'hot_vitality', 'magnitude': 5.0}]),
            char, 1)
        # Second component would win its lane; the first is refused —
        # the whole application refuses, nothing mutates.
        multi = make_effect('admJ-multi', [
            {'ctype': 'hot_vitality', 'magnitude': 2.0},
            {'ctype': 'dot_longevity', 'magnitude': 10.0},
        ])
        before = len(active_instances(char))
        with self.assertRaises(EffectRefused) as ctx:
            apply_effect_definition(multi, char, 1)
        self.assertEqual(ctx.exception.blocking_name, 'admJ-inc Effect')
        self.assertEqual(len(active_instances(char)), before)
        self.assertFalse(EffectInstance.objects.filter(
            definition=multi).exists())

    def test_curse_incumbent_never_blocks(self):
        char = self._world('admK')
        curse = make_effect(
            'admK-curse', [{'ctype': 'dot_vitality', 'magnitude': 100.0}],
            is_curse=True)
        _create_effect_instance(curse, char, 1)
        # A live curse is excluded from the incumbent comparison set.
        apply_effect_definition(
            make_effect('admK-ord', [{'ctype': 'dot_vitality', 'magnitude': 2.0}]),
            char, 1)
        self.assertEqual(len(active_instances(char)), 2)


# ----------------------------------------------------------------------
# §12.2 — refusal surfacing
# ----------------------------------------------------------------------

class RefusalSurfacingTests(TransactionTestCase):

    async def test_use_path_keeps_the_consumable_and_warns(self):
        def setup():
            zone, room = make_world('refA')
            char = make_character('refA', room)
            set_bars(char, vitality_current=50)
            strong = make_effect(
                'refA-strong', [{'ctype': 'hot_vitality', 'magnitude': 6.0}])
            apply_effect_definition(strong, char, 1)
            weak = make_effect(
                'refA-weak', [{'ctype': 'hot_vitality', 'magnitude': 3.0}])
            salve_def = make_item_def('refA', 'Weak Salve', 'consumable',
                                      effect=weak)
            make_owned_item(salve_def, char)
            # The stub consumer reads char.user; warm the FK cache here
            # in sync context (refresh_from_db would have cleared it).
            return Character.objects.select_related('user').get(pk=char.pk)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('weak salve')
        msgs = outputs(sent)
        warns = [m for m in msgs if m['category'] == 'warn']
        self.assertEqual(len(warns), 1)
        self.assertIn('refA-strong Effect', warns[0]['text'])
        self.assertIn('would be wasted', warns[0]['text'])
        count = await sync_to_async(
            lambda: ItemInstance.objects.filter(owner=char).count())()
        self.assertEqual(count, 1)

    def test_npc_path_skips_silently(self):
        zone, room = make_world('refB')
        char = make_character('refB', room)
        strong = make_effect(
            'refB-strong', [{'ctype': 'dot_vitality', 'magnitude': 50.0}])
        apply_effect_definition(strong, char, 1)
        weak = make_effect(
            'refB-poison', [{'ctype': 'dot_vitality', 'magnitude': 3.0}])
        definition = make_npc_definition('refB')
        npc = make_npc(definition, room)
        NpcEffect.objects.create(
            npc_definition=definition, effect_definition=weak,
            effect_chance=1.0)
        messages, candidates = apply_npc_effects_detailed(npc, char)
        self.assertEqual(messages, [])
        self.assertTrue(candidates[0]['fired'])
        self.assertFalse(EffectInstance.objects.filter(
            definition=weak, target=char).exists())
        # With the blocker gone, the same proc lands and names itself.
        EffectComponentInstance.objects.filter(
            effect_instance__definition=strong).update(is_active=False)
        EffectInstance.objects.filter(definition=strong).update(is_active=False)
        messages, _ = apply_npc_effects_detailed(npc, char)
        self.assertIn('refB-poison Effect', messages)


# ----------------------------------------------------------------------
# §12.3 — the #331 staleness fix
# ----------------------------------------------------------------------

class StalenessTests(TransactionTestCase):

    async def test_two_hots_cumulative_with_apply_order(self):
        def setup():
            zone, room = make_world('stA')
            char = make_character('stA', room)
            enter_combat(char, room)
            set_bars(char, vitality_current=50, vitality_max=100)
            apply_effect_definition(
                make_effect('stA-w', [{'ctype': 'hot_vitality', 'magnitude': 3.0}]),
                char, 1)
            apply_effect_definition(
                make_effect('stA-s', [{'ctype': 'hot_vitality', 'magnitude': 6.0}]),
                char, 1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()
        await cmd.process_effects(3)
        rows = [(t, c) for pk, t, c in msgs if pk == char.pk]
        self.assertEqual(rows, [
            ('You recover 3 Vitality from stA-w Effect.', 'system'),
            ('You recover 6 Vitality from stA-s Effect.', 'system'),
        ])
        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).vitality_current)()
        self.assertEqual(current, 59)

        # Near-full: the second component tops out on the state the
        # first left behind; the arrival is the terminal line.
        await sync_to_async(set_bars)(char, vitality_current=96)
        msgs.clear()
        await cmd.process_effects(6)
        rows = [(t, c) for pk, t, c in msgs if pk == char.pk]
        self.assertEqual(rows, [
            ('You recover 3 Vitality from stA-w Effect.', 'system'),
            ('Your body is whole once more. (+1 Vitality)', 'system'),
        ])

        # Full: both silent.
        msgs.clear()
        await cmd.process_effects(9)
        self.assertEqual([(t, c) for pk, t, c in msgs if pk == char.pk], [])

    async def test_two_dots_cumulative(self):
        def setup():
            zone, room = make_world('stB')
            char = make_character('stB', room)
            enter_combat(char, room)
            set_bars(char, vitality_current=100, vitality_max=100)
            apply_effect_definition(
                make_effect('stB-1', [{'ctype': 'dot_vitality', 'magnitude': 10.0}]),
                char, 1)
            apply_effect_definition(
                make_effect('stB-2', [{'ctype': 'dot_vitality', 'magnitude': 11.0}]),
                char, 1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()
        await cmd.process_effects(3)
        rows = [(t, c) for pk, t, c in msgs if pk == char.pk]
        self.assertEqual(rows, [
            ('You take 10 damage from stB-1 Effect.', 'combat'),
            ('You take 11 damage from stB-2 Effect.', 'combat'),
        ])
        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).vitality_current)()
        self.assertEqual(current, 79)


# ----------------------------------------------------------------------
# §12.4 — generation
# ----------------------------------------------------------------------

class GenerationTests(TestCase):

    def setUp(self):
        self.zone, self.room = make_world('gen')
        self.char = make_character('gen', self.room)
        self.curse = make_effect(
            'gen-curse', [{'ctype': 'dot_vitality', 'magnitude': 2.0}],
            is_curse=True)
        self.pool_def = ItemDefinition.objects.create(
            name='gen Blade', slug='gen-blade', item_type='weapon',
            genre_tag='fantasy', valid_slots=['MAIN_HAND'],
            scaling_base=1.0, scaling_factor=1.0,
            takes_durability_loss=False, durability_table=[],
            is_cursed_template=True,
        )
        CurseCandidate.objects.create(
            item_definition=self.pool_def, curse=self.curse, weight=1)

    def test_natural_roll_never_fires_at_zero_chance(self):
        for _ in range(10):
            item = generate_item_instance(self.pool_def, 1, 'rare')
            self.assertIsNone(item.latent_curse)
            self.assertFalse(item.is_cursed)

    def test_force_rolls_from_pool_and_bypasses_rarity_gate(self):
        item = generate_item_instance(
            self.pool_def, 1, 'common', owner=self.char, gift=True,
            force_curse=True)
        self.assertEqual(item.latent_curse, self.curse)
        self.assertTrue(item.is_cursed)
        self.assertTrue(item.is_soulbound)

    def test_force_respects_explicit_override(self):
        other = make_effect(
            'gen-other', [{'ctype': 'dot_longevity', 'magnitude': 2.0}],
            is_curse=True)
        item = generate_item_instance(
            self.pool_def, 1, 'rare', force_curse=True, curse=other)
        self.assertEqual(item.latent_curse, other)

    def test_force_refuses_non_curse_override(self):
        ordinary = make_effect(
            'gen-ord', [{'ctype': 'hot_vitality', 'magnitude': 2.0}])
        with self.assertRaises(ValueError):
            generate_item_instance(
                self.pool_def, 1, 'rare', force_curse=True, curse=ordinary)

    def test_force_refuses_empty_pool(self):
        bare = ItemDefinition.objects.create(
            name='gen Bare', slug='gen-bare', item_type='weapon',
            genre_tag='fantasy', valid_slots=['MAIN_HAND'],
            scaling_base=1.0, scaling_factor=1.0,
            takes_durability_loss=False, durability_table=[],
        )
        with self.assertRaises(ValueError):
            generate_item_instance(bare, 1, 'rare', force_curse=True)

    def test_natural_gate_logic_with_patched_chance(self):
        with mock.patch('apps.shyland.item_utils.CURSE_WILD_CHANCE', 1.0):
            rare = generate_item_instance(self.pool_def, 1, 'rare')
            self.assertEqual(rare.latent_curse, self.curse)
            self.assertTrue(rare.is_cursed)
            # Common never rolls cursed on the natural path.
            common = generate_item_instance(self.pool_def, 1, 'common')
            self.assertIsNone(common.latent_curse)
            # Non-template definitions never roll.
            bare = ItemDefinition.objects.create(
                name='gen Plain', slug='gen-plain', item_type='weapon',
                genre_tag='fantasy', valid_slots=['MAIN_HAND'],
                scaling_base=1.0, scaling_factor=1.0,
                takes_durability_loss=False, durability_table=[],
            )
            plain = generate_item_instance(bare, 1, 'rare')
            self.assertIsNone(plain.latent_curse)


# ----------------------------------------------------------------------
# §12.5 — the trap
# ----------------------------------------------------------------------

class TrapTests(TestCase):

    def setUp(self):
        self.zone, self.room = make_world('trap')
        self.char = make_character('trap', self.room)

    def test_spring_populates_and_returns_theater_in_order(self):
        curse = make_effect(
            'trapA', [{'ctype': 'dot_vitality', 'magnitude': 2.0}],
            is_curse=True,
            apply_text='First line.\n\nSecond line.\n')
        item = make_latent_item('trapA', self.char, curse)
        lines = spring_curse(item, self.char)
        self.assertEqual(lines, ['First line.', 'Second line.'])
        item.refresh_from_db()
        self.assertIsNotNone(item.active_curse)
        self.assertTrue(item.curse_identified)
        self.assertTrue(item.active_curse.is_active)
        self.assertEqual(item.active_curse.mk_tier, item.mk_tier)
        # The latent stays set until curse end; soulbind untouched.
        self.assertEqual(item.latent_curse, curse)
        self.assertFalse(item.is_soulbound)

    def test_spring_bypasses_every_gate(self):
        # A stronger same-lane incumbent would refuse an ordinary apply.
        apply_effect_definition(
            make_effect('trapB-inc', [{'ctype': 'dot_vitality', 'magnitude': 50.0}]),
            self.char, 1)
        curse = make_effect(
            'trapB', [{'ctype': 'dot_vitality', 'magnitude': 2.0}],
            is_curse=True)
        item = make_latent_item('trapB', self.char, curse)
        spring_curse(item, self.char)
        item.refresh_from_db()
        self.assertIsNotNone(item.active_curse)

    def test_guard_fires_only_once(self):
        curse = make_effect(
            'trapC', [{'ctype': 'dot_vitality', 'magnitude': 2.0}],
            is_curse=True, apply_text='Theater.')
        item = make_latent_item('trapC', self.char, curse)
        first = spring_if_latent(None, item, self.char)
        self.assertEqual(first, ['Theater.'])
        item.refresh_from_db()
        second = spring_if_latent(None, item, self.char)
        self.assertEqual(second, [])

    def test_two_same_curse_items_spring_independently(self):
        curse = make_effect(
            'trapD', [{'ctype': 'dot_vitality', 'magnitude': 2.0}],
            is_curse=True)
        item_a = make_latent_item('trapD-a', self.char, curse)
        item_b = make_latent_item('trapD-b', self.char, curse)
        spring_curse(item_a, self.char)
        spring_curse(item_b, self.char)
        self.assertEqual(EffectInstance.objects.filter(
            definition=curse, target=self.char, is_active=True).count(), 2)


# ----------------------------------------------------------------------
# §12.6 — the component types (sync half)
# ----------------------------------------------------------------------

class ComponentTests(TestCase):

    def setUp(self):
        self.zone, self.room = make_world('cmp')
        self.char = make_character('cmp', self.room)

    def test_stat_cut_exact_reversal_after_mid_curse_change(self):
        self.assertEqual(self.char.stat_str, 10)
        definition = make_effect(
            'cmpA', [{'ctype': 'stat_cut_percent', 'magnitude': 0.25,
                      'target_stat': 'str'}])
        apply_effect_definition(definition, self.char, 1)
        self.char.refresh_from_db()
        # delta = int(0.25 × 10) = 2, stored negative on the instance.
        self.assertEqual(self.char.stat_str, 8)
        ci = EffectComponentInstance.objects.get(
            effect_instance__definition=definition)
        self.assertEqual(ci.magnitude, -2)
        # A mid-curse stat change does not disturb the stored delta.
        self.char.stat_str = 13
        self.char.save(update_fields=['stat_str'])
        apply_stat_effect(self.char, ci, reverse=True)
        self.char.refresh_from_db()
        self.assertEqual(self.char.stat_str, 15)

    def test_bar_cut_applies_and_reverses_under_the_bar_law(self):
        rescale_bars_for_gear(self.char)
        self.char.refresh_from_db()
        base_max = self.char.vitality_max          # 10×10 + 10×3 + 5 = 135
        self.assertEqual(base_max, 135)
        set_bars(self.char, vitality_current=67)

        curse = make_effect(
            'cmpB', [{'ctype': 'cut_vitality_max', 'magnitude': 0.2,
                      'no_expiry': True}],
            is_curse=True, memorial_text='Scarred.')
        item = make_latent_item('cmpB', self.char, curse)
        spring_curse(item, self.char)
        self.char.refresh_from_db()
        cut_max = base_max - int(0.2 * base_max)   # 135 - 27 = 108
        self.assertEqual(self.char.vitality_max, cut_max)
        # Fill fraction preserved (67/135 → ~54/108, rounded).
        self.assertIn(self.char.vitality_current, (53, 54))

        # A mid-curse rescale (gear equip shape) keeps the cut.
        rescale_bars_for_gear(self.char)
        self.char.refresh_from_db()
        self.assertEqual(self.char.vitality_max, cut_max)

        held = self.char.vitality_current
        end_curse(item, 'timeout')
        self.char.refresh_from_db()
        self.assertEqual(self.char.vitality_max, base_max)
        expected = round(held * base_max / cut_max)
        self.assertIn(self.char.vitality_current,
                      (expected - 1, expected, expected + 1))

    def test_combat_factors_multiply(self):
        for magnitude in (0.2, 0.5):
            _create_effect_instance(
                make_effect(f'cmpC-{int(magnitude*10)}',
                            [{'ctype': 'damage_cut', 'magnitude': magnitude,
                              'no_expiry': True}], is_curse=True),
                self.char, 1)
        _create_effect_instance(
            make_effect('cmpC-armor',
                        [{'ctype': 'armor_cut', 'magnitude': 0.3,
                          'no_expiry': True}], is_curse=True),
            self.char, 1)
        dmg, armor = curse_combat_reads(self.char)
        self.assertAlmostEqual(dmg, 0.4)
        self.assertAlmostEqual(armor, 0.7)

    def test_vitality_hold_value_reads_the_hold(self):
        self.assertIsNone(vitality_hold_value(self.char))
        _create_effect_instance(
            make_effect('cmpD',
                        [{'ctype': 'floor_hold_vitality', 'magnitude': 8.0,
                          'mag2': 0.05, 'mag2_scale': 0.0,
                          'no_expiry': True}], is_curse=True),
            self.char, 1)
        # ceil(0.05 × 100) = 5 on the default max.
        self.assertEqual(vitality_hold_value(self.char), 5)

    def test_instant_restore_honors_the_heal_ceiling(self):
        _create_effect_instance(
            make_effect('cmpE-hold',
                        [{'ctype': 'floor_hold_vitality', 'magnitude': 8.0,
                          'mag2': 0.05, 'mag2_scale': 0.0,
                          'no_expiry': True}], is_curse=True),
            self.char, 1)
        heal = make_effect(
            'cmpE-heal', [{'ctype': 'restore_vitality', 'magnitude': 25.0,
                           'duration': 0.0}])
        # Below the hold: heals work up to the hold.
        set_bars(self.char, vitality_current=3)
        apply_effect_definition(heal, self.char, 1)
        self.char.refresh_from_db()
        self.assertEqual(self.char.vitality_current, 5)
        # Above the hold: heals are no-ops.
        set_bars(self.char, vitality_current=8)
        apply_effect_definition(heal, self.char, 1)
        self.char.refresh_from_db()
        self.assertEqual(self.char.vitality_current, 8)


# ----------------------------------------------------------------------
# §12.6 — the floor hold under the engine
# ----------------------------------------------------------------------

class FloorHoldEngineTests(TransactionTestCase):

    def _setup(self, prefix, vitality, magnitude=8.0):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        enter_combat(char, room)
        set_bars(char, vitality_current=vitality, vitality_max=100)
        curse = make_effect(
            f'{prefix}-hold',
            [{'ctype': 'floor_hold_vitality', 'magnitude': magnitude,
              'mag2': 0.05, 'mag2_scale': 0.0, 'no_expiry': True}],
            is_curse=True)
        _create_effect_instance(curse, char, 1)
        return char

    async def test_drain_arrival_line_then_pin_silence(self):
        char = await sync_to_async(self._setup)('fhA', 20)
        cmd, msgs = run_effects_engine()
        await cmd.process_effects(3)
        rows = [(t, c) for pk, t, c in msgs if pk == char.pk]
        self.assertEqual(rows, [
            ('You take 8 damage from fhA-hold Effect.', 'combat')])
        msgs.clear()
        await cmd.process_effects(6)
        rows = [(t, c) for pk, t, c in msgs if pk == char.pk]
        # 12 → 5: the arrival terminal line, actual delta.
        self.assertEqual(rows, [
            ('fhA-hold Effect holds your life at its lowest ebb. '
             '(-7 Vitality)', 'combat')])
        msgs.clear()
        await cmd.process_effects(9)
        self.assertEqual([(t, c) for pk, t, c in msgs if pk == char.pk], [])
        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).vitality_current)()
        self.assertEqual(current, 5)

    async def test_never_kills_and_below_hold_is_silent(self):
        char = await sync_to_async(self._setup)('fhB', 100, magnitude=500.0)
        cmd, msgs = run_effects_engine()
        await cmd.process_effects(3)
        state = await sync_to_async(
            lambda: (Character.objects.get(pk=char.pk).vitality_current,
                     Character.objects.get(pk=char.pk).is_dying))()
        self.assertEqual(state, (5, False))
        # Combat damage below the hold: the drain never follows it down.
        await sync_to_async(set_bars)(char, vitality_current=2)
        msgs.clear()
        await cmd.process_effects(6)
        self.assertEqual([(t, c) for pk, t, c in msgs if pk == char.pk], [])
        state = await sync_to_async(
            lambda: (Character.objects.get(pk=char.pk).vitality_current,
                     Character.objects.get(pk=char.pk).is_dying))()
        self.assertEqual(state, (2, False))

    async def test_hot_heals_up_to_the_hold_only(self):
        char = await sync_to_async(self._setup)('fhC', 2)
        await sync_to_async(apply_effect_definition)(
            await sync_to_async(make_effect)(
                'fhC-mend', [{'ctype': 'hot_vitality', 'magnitude': 6.0}]),
            char, 1)
        cmd, msgs = run_effects_engine()
        await cmd.process_effects(3)
        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).vitality_current)()
        # Below the hold the hot works up to it: 2 → 5, never past.
        self.assertEqual(current, 5)
        msgs.clear()
        await cmd.process_effects(6)
        # At the hold the hot is a silent no-op (change-only).
        rows = [(t, c) for pk, t, c in msgs if pk == char.pk]
        self.assertEqual(rows, [])


class AggregateHealCeilingTests(TransactionTestCase):
    """v26.2 (#330): the heal ceiling on the third vitality-write path —
    the #151 aggregate (`use`/`heal`), which writes vitality through its
    own atomic UPDATE rather than _apply_instant_component. Found during
    playtest prep, fixed in-session."""

    async def test_aggregate_heals_to_the_hold_and_never_past(self):
        def setup():
            zone, room = make_world('aggA')
            char = make_character('aggA', room)
            set_bars(char, vitality_current=3, vitality_max=100)
            _create_effect_instance(
                make_effect('aggA-hold',
                            [{'ctype': 'floor_hold_vitality', 'magnitude': 8.0,
                              'mag2': 0.05, 'mag2_scale': 0.0,
                              'no_expiry': True}], is_curse=True),
                char, 1)
            heal = make_effect(
                'aggA-heal', [{'ctype': 'restore_vitality', 'magnitude': 25.0,
                               'duration': 0.0}])
            draught_def = make_item_def('aggA', 'Healing Draught',
                                        'consumable', effect=heal)
            for _ in range(3):
                make_owned_item(draught_def, char)
            return (Character.objects.select_related('user').get(pk=char.pk),
                    draught_def)
        char, draught_def = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('3 healing draught')
        state = await sync_to_async(
            lambda: (Character.objects.get(pk=char.pk).vitality_current,
                     ItemInstance.objects.filter(
                         owner=char, definition=draught_def).count()))()
        # Below the hold: heals up to the hold (3 -> 5); planning stops
        # at the effective headroom — ONE draught consumed, not three.
        self.assertEqual(state, (5, 2))
        # The full-heal fold never fires under a hold.
        texts = [m['text'] for m in outputs(sent)]
        self.assertFalse(any('full health' in t for t in texts))

        # At the hold: the draught is consumed, the heal is a no-op.
        sent.clear()
        await consumer.cmd_use('healing draught')
        state = await sync_to_async(
            lambda: (Character.objects.get(pk=char.pk).vitality_current,
                     ItemInstance.objects.filter(
                         owner=char, definition=draught_def).count()))()
        self.assertEqual(state, (5, 1))


# ----------------------------------------------------------------------
# §12.7 — lifecycle
# ----------------------------------------------------------------------

class LifecycleTests(TransactionTestCase):

    def _sprung(self, prefix, components, **kwargs):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        curse = make_effect(f'{prefix}-curse', components, is_curse=True,
                            **kwargs)
        item = make_latent_item(prefix, char, curse)
        spring_curse(item, char)
        item.refresh_from_db()
        return char, item

    async def test_expiry_cleans_everything(self):
        def setup():
            char, item = self._sprung(
                'lcA',
                [{'ctype': 'stat_cut_percent', 'magnitude': 0.25,
                  'target_stat': 'str', 'duration': 60.0}],
                memorial_text='A scar remains.')
            char.refresh_from_db()
            assert char.stat_str == 8
            EffectComponentInstance.objects.filter(
                effect_instance=item.active_curse).update(
                expires_at=timezone.now() - timedelta(seconds=1))
            return char, item
        char, item = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()
        await cmd.process_effects(1)

        def state():
            item.refresh_from_db()
            char.refresh_from_db()
            instance = EffectInstance.objects.get(
                definition__slug='lcA-curse-effect')
            return (item.is_cursed, item.latent_curse, item.active_curse,
                    item.memorial_description, char.stat_str,
                    instance.is_active, instance.removed_by)
        (cursed, latent, active, memorial, stat, ei_active,
         removed_by) = await sync_to_async(state)()
        self.assertFalse(cursed)
        self.assertIsNone(latent)
        self.assertIsNone(active)
        self.assertEqual(memorial, 'A scar remains.')
        self.assertEqual(stat, 10)
        self.assertFalse(ei_active)
        self.assertEqual(removed_by, 'timeout')
        rows = [t for pk, t, c in msgs if pk == char.pk]
        self.assertIn('lcA-curse Effect is spent. Its hold on you breaks.',
                      rows)

    def test_clean_item_is_free_and_springs_nothing(self):
        char, item = self._sprung(
            'lcB', [{'ctype': 'dot_vitality', 'magnitude': 1.0,
                     'duration': 60.0}],
            memorial_text='Quiet now.')
        self.assertIsNotNone(unequip_blocked(None, item, [], 0))
        end_curse(item, 'timeout')
        item.refresh_from_db()
        self.assertIsNone(unequip_blocked(None, item, [], 0))
        self.assertEqual(spring_if_latent(None, item, char), [])

    def test_memorial_rides_the_description_chokepoint(self):
        zone, room = make_world('lcC')
        char = make_character('lcC', room)
        defn = make_item_def('lcC', 'Old Blade', 'weapon')
        item = make_owned_item(defn, char)
        item.memorial_description = 'It is quiet now.'
        item.save(update_fields=['memorial_description'])
        self.assertTrue(
            get_display_description(item).endswith('It is quiet now.'))

    def test_sudo_teardown_cleans_the_latent_flag(self):
        char, item = self._sprung(
            'lcD', [{'ctype': 'dot_vitality', 'magnitude': 1.0,
                     'duration': 60.0}],
            memorial_text='Kept.')
        instance_pk = item.active_curse_id
        end_curse(item, 'item-removed')
        item.refresh_from_db()
        self.assertFalse(item.is_cursed)
        self.assertIsNone(item.latent_curse)
        self.assertIsNone(item.active_curse)
        self.assertEqual(item.memorial_description, 'Kept.')
        instance = EffectInstance.objects.get(pk=instance_pk)
        self.assertFalse(instance.is_active)
        self.assertEqual(instance.removed_by, 'item-removed')
        self.assertFalse(instance.component_instances.filter(
            is_active=True).exists())


# ----------------------------------------------------------------------
# §12.8 — death semantics
# ----------------------------------------------------------------------

class DeathSemanticsTests(TransactionTestCase):

    async def test_curse_dot_fall_ends_only_the_killing_curse(self):
        def setup():
            zone, room = make_world('dsA')
            char = make_character('dsA', room)
            enter_combat(char, room)
            set_bars(char, vitality_current=5, vitality_max=100)
            killer = make_effect(
                'dsA-killer', [{'ctype': 'dot_vitality', 'magnitude': 10.0,
                                'no_expiry': True}],
                is_curse=True, memorial_text='It took what it came for.')
            killer_item = make_latent_item('dsA-k', char, killer)
            spring_curse(killer_item, char)
            bystander = make_effect(
                'dsA-stander', [{'ctype': 'damage_cut', 'magnitude': 0.2,
                                 'no_expiry': True}],
                is_curse=True)
            bystander_item = make_latent_item('dsA-b', char, bystander)
            spring_curse(bystander_item, char)
            ordinary = make_effect(
                'dsA-ord', [{'ctype': 'hot_longevity', 'magnitude': 2.0}])
            apply_effect_definition(ordinary, char, 1)
            return char, killer_item, bystander_item
        char, killer_item, bystander_item = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()
        await cmd.process_effects(3)

        def state():
            killer_item.refresh_from_db()
            bystander_item.refresh_from_db()
            char.refresh_from_db()
            ordinary_instance = EffectInstance.objects.get(
                definition__slug='dsA-ord-effect')
            killer_instance = EffectInstance.objects.get(
                definition__slug='dsA-killer-effect')
            return (char.is_dying, killer_item.is_cursed,
                    killer_item.memorial_description,
                    killer_instance.removed_by,
                    bystander_item.is_cursed,
                    EffectInstance.objects.get(
                        definition__slug='dsA-stander-effect').is_active,
                    ordinary_instance.is_active,
                    ordinary_instance.removed_by)
        (is_dying, killer_cursed, memorial, killer_removed,
         bystander_cursed, bystander_active, ordinary_active,
         ordinary_removed) = await sync_to_async(state)()
        self.assertTrue(is_dying)
        self.assertFalse(killer_cursed)
        self.assertEqual(memorial, 'It took what it came for.')
        self.assertEqual(killer_removed, 'curse-death')
        self.assertTrue(bystander_cursed)
        self.assertTrue(bystander_active)
        self.assertFalse(ordinary_active)
        self.assertEqual(ordinary_removed, 'dying')

    async def test_other_cause_death_curse_persists_refill_to_cut_max(self):
        def setup():
            zone, room = make_world('dsB')
            char = make_character('dsB', room)
            rescale_bars_for_gear(char)
            char.refresh_from_db()
            curse = make_effect(
                'dsB-cut', [{'ctype': 'cut_vitality_max', 'magnitude': 0.2,
                             'no_expiry': True}],
                is_curse=True)
            item = make_latent_item('dsB', char, curse)
            spring_curse(item, char)
            char.refresh_from_db()
            cut_max = char.vitality_max          # 135 - 27 = 108
            assert cut_max == 108
            Character.objects.filter(pk=char.pk).update(
                vitality_current=0, is_dying=True,
                dying_since=timezone.now() - timedelta(
                    seconds=DYING_DURATION_SECS + 5))
            return char, item, cut_max
        char, item, cut_max = await sync_to_async(setup)()
        cmd = make_engine()
        await cmd.process_combat(1)

        def state():
            char.refresh_from_db()
            item.refresh_from_db()
            return (char.is_dying, char.vitality_current, char.vitality_max,
                    item.is_cursed,
                    item.active_curse.is_active if item.active_curse else None)
        (is_dying, current, maximum, cursed,
         curse_active) = await sync_to_async(state)()
        self.assertFalse(is_dying)
        self.assertTrue(cursed)
        self.assertTrue(curse_active)
        # The refill fills to the CUT max — the cut was not reversed.
        self.assertEqual(maximum, cut_max)
        self.assertEqual(current, cut_max)
