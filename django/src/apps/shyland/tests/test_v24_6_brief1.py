"""V24.6 Brief 1 (#177, #178): the composite strike.

Every equipped, non-broken weapon contributes to one strike per round:
the primary (first occupied slot in MAIN_HAND -> RANGED -> OFF_HAND
order) at factor 1.0, every other weapon at its slot factor (0.5 first
pass). Per-weapon terms carry their own damage roll, governing stat
(DEX for ranged weapons, STR otherwise), and durability; acuity and the
graze/crit multiplier apply once, to the composite. The unarmed path is
untouched. Ranged-slot semantics (#178): "at the ready" — the weapon's
participation in every round's composite is the ruling made real; the
equip resolver is unchanged.
"""

from asgiref.sync import sync_to_async
from unittest import mock

from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland.combat_utils import (
    PRIMARY_WEAPON_SLOT_PRIORITY, SECONDARY_WEAPON_FACTOR_DEFAULT,
    SECONDARY_WEAPON_SLOT_FACTOR, composite_weapon_term, effective_stats,
)
from apps.shyland.models import ItemDefinition, ItemInstance, NpcInstance

from .test_gear_combat import make_combat_world, run_engine_round


def midpoint_uniform(a, b):
    return (a + b) / 2.0


class MemDef:
    def __init__(self, is_ranged=False, takes_durability=False, table=None):
        self.is_ranged = is_ranged
        self.takes_durability_loss = takes_durability
        self.durability_table = table if table is not None else []


class MemWeapon:
    """In-memory stand-in: the helper reads equipped_slot, the damage
    fields, durability, and definition.is_ranged only."""

    def __init__(self, slot, midpoint, spread=0.0, is_ranged=False,
                 durability=100.0, takes_durability=False, table=None):
        self.definition = MemDef(is_ranged, takes_durability, table)
        self.equipped_slot = slot
        self.damage_midpoint = midpoint
        self.damage_spread = spread
        self.durability_current = durability


STR, DEX = 5, 3


def term(weapons):
    """The composite term with every damage roll pinned to its midpoint."""
    with mock.patch('apps.shyland.combat_utils.random.uniform',
                    side_effect=midpoint_uniform):
        return composite_weapon_term(weapons, STR, DEX)


class CompositeTermTests(SimpleTestCase):

    def test_constants_are_the_ruled_values(self):
        self.assertEqual(PRIMARY_WEAPON_SLOT_PRIORITY,
                         ('MAIN_HAND', 'RANGED', 'OFF_HAND'))
        self.assertEqual(SECONDARY_WEAPON_SLOT_FACTOR,
                         {'OFF_HAND': 0.5, 'RANGED': 0.5})
        self.assertEqual(SECONDARY_WEAPON_FACTOR_DEFAULT, 0.5)

    def test_main_hand_is_primary_over_ranged_and_off_hand(self):
        weapons = [MemWeapon('OFF_HAND', 6),
                   MemWeapon('RANGED', 8, is_ranged=True),
                   MemWeapon('MAIN_HAND', 10)]
        # 1.0x(10+STR) + 0.5x(8+DEX) + 0.5x(6+STR)
        self.assertAlmostEqual(term(weapons), 15 + 5.5 + 5.5)

    def test_ranged_is_primary_over_off_hand(self):
        weapons = [MemWeapon('OFF_HAND', 6),
                   MemWeapon('RANGED', 8, is_ranged=True)]
        # 1.0x(8+DEX) + 0.5x(6+STR)
        self.assertAlmostEqual(term(weapons), 11 + 5.5)

    def test_sole_off_hand_weapon_is_primary_at_full_factor(self):
        # A bow-only or off-hand-only loadout fights at full strength.
        self.assertAlmostEqual(term([MemWeapon('OFF_HAND', 6)]), 11.0)

    def test_ranged_term_uses_dex_melee_uses_str(self):
        # Identical midpoints differ by exactly the governing stat.
        self.assertAlmostEqual(term([MemWeapon('MAIN_HAND', 10)]), 15.0)
        self.assertAlmostEqual(
            term([MemWeapon('RANGED', 10, is_ranged=True)]), 13.0)

    def test_each_weapon_rolls_within_its_own_band(self):
        with mock.patch('apps.shyland.combat_utils.random.uniform',
                        side_effect=midpoint_uniform) as rng:
            composite_weapon_term(
                [MemWeapon('MAIN_HAND', 10, spread=2.0),
                 MemWeapon('OFF_HAND', 6)], STR, DEX)
        rng.assert_any_call(8.0, 12.0)
        rng.assert_any_call(6, 6)

    def test_damaged_weapon_reduces_only_its_own_term(self):
        table = [{'min': 0, 'max': 100, 'penalty': 0.25}]
        weapons = [MemWeapon('MAIN_HAND', 10),
                   MemWeapon('OFF_HAND', 6, durability=50.0,
                             takes_durability=True, table=table)]
        # The main-hand term is untouched; only the off-hand term x0.75.
        self.assertAlmostEqual(term(weapons), 15 + 5.5 * 0.75)

    def test_priority_falls_through_when_higher_slots_absent(self):
        # The engine filters broken weapons before the call — a broken
        # main hand means MAIN_HAND simply isn't occupied here, and the
        # next slot in priority is primary.
        weapons = [MemWeapon('RANGED', 8, is_ranged=True),
                   MemWeapon('OFF_HAND', 6)]
        self.assertAlmostEqual(term(weapons), 11 + 5.5)

    def test_two_hander_plus_ranged(self):
        # The Battle Axe + Pulse Pistol shape: the axe occupies MAIN_HAND
        # (a two-hander claims both hands but sits in one slot) and is
        # primary; the pistol contributes at 0.5.
        weapons = [MemWeapon('MAIN_HAND', 12),
                   MemWeapon('RANGED', 8, is_ranged=True)]
        self.assertAlmostEqual(term(weapons), 17 + 5.5)

    def test_unknown_slot_defaults_to_secondary_factor_no_crash(self):
        # Defensive case: a slot in neither constant never crashes the
        # tick engine and contributes at the secondary default 0.5.
        self.assertAlmostEqual(term([MemWeapon('TENTACLE', 6)]), 5.5)
        weapons = [MemWeapon('MAIN_HAND', 10), MemWeapon('TENTACLE', 6)]
        self.assertAlmostEqual(term(weapons), 15 + 5.5)

    def test_empty_weapon_list_is_zero(self):
        self.assertEqual(composite_weapon_term([], STR, DEX), 0.0)


def make_weapon_def(prefix, name, is_ranged=False, two_handed=False):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type='weapon', genre_tag='fantasy',
        valid_slots=['RANGED'] if is_ranged else ['MAIN_HAND'],
        scaling_base=0.0, scaling_factor=0.0, base_value=1,
        is_ranged=is_ranged, is_two_handed=two_handed,
        # The model default is True with an empty durability_table, and
        # an empty table reads as the full 1.0 penalty — durability-free
        # test weapons keep the terms at full strength.
        takes_durability_loss=False,
    )


def equip_weapon(defn, char, slot, midpoint, spread=0.0, broken=False):
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity='common',
        durability_current=0.0 if broken else 100.0, is_broken=broken,
        is_identified=True, is_equipped=True, equipped_slot=slot,
        damage_midpoint=midpoint, damage_spread=spread,
    )


class EngineCompositeTests(TransactionTestCase):
    """The tick engine feeds the composite term through calculate_damage
    as base_damage with stat_bonus=0 and durability_mod=1.0 — stat and
    durability live inside the per-weapon terms; acuity and the hit
    multiplier apply once, to the whole."""

    async def test_round_damage_is_the_composite_of_all_weapons(self):
        def setup():
            char, npc = make_combat_world('vcA')
            mace = make_weapon_def('vcA', 'Test Mace')
            knife = make_weapon_def('vcA', 'Test Knife')
            equip_weapon(mace, char, 'MAIN_HAND', 10.0)
            equip_weapon(knife, char, 'OFF_HAND', 6.0)
            return char, npc, effective_stats(char)
        char, npc, eff = await sync_to_async(setup)()

        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='hit'), \
             mock.patch('apps.shyland.combat_utils.acuity_damage_modifier',
                        return_value=1.0), \
             mock.patch('apps.shyland.combat_utils.random.uniform',
                        side_effect=midpoint_uniform):
            await cmd.process_combat(1)

        expected = int((10.0 + eff['str']) + 0.5 * (6.0 + eff['str']))
        out_hits = [t for _, t, c in player_msgs if c == 'combat-hit-out']
        self.assertTrue(out_hits)
        self.assertTrue(out_hits[0].startswith('You hit'))
        self.assertIn(f'for {expected} damage', out_hits[0])

        def npc_vit():
            return NpcInstance.objects.get(pk=npc.pk).vitality_current
        self.assertEqual(await sync_to_async(npc_vit)(), 1000 - expected)

    async def test_broken_primary_falls_to_ranged_at_full_strength(self):
        def setup():
            char, npc = make_combat_world('vcB')
            mace = make_weapon_def('vcB', 'Test Mace')
            pistol = make_weapon_def('vcB', 'Test Pistol', is_ranged=True)
            equip_weapon(mace, char, 'MAIN_HAND', 10.0, broken=True)
            equip_weapon(pistol, char, 'RANGED', 8.0)
            return char, npc, effective_stats(char)
        char, npc, eff = await sync_to_async(setup)()

        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='hit'), \
             mock.patch('apps.shyland.combat_utils.acuity_damage_modifier',
                        return_value=1.0), \
             mock.patch('apps.shyland.combat_utils.random.uniform',
                        side_effect=midpoint_uniform):
            await cmd.process_combat(1)

        # The broken mace contributes nothing; the pistol is primary at
        # 1.0 and its term is DEX-governed. Armed flavor, not unarmed.
        expected = int(8.0 + eff['dex'])
        out_hits = [t for _, t, c in player_msgs if c == 'combat-hit-out']
        self.assertTrue(out_hits)
        self.assertTrue(out_hits[0].startswith('You hit'))
        self.assertIn(f'for {expected} damage', out_hits[0])

    async def test_unarmed_path_unchanged_with_zero_weapons(self):
        char, npc = await sync_to_async(make_combat_world)('vcC')
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='hit'):
            await cmd.process_combat(1)

        # No equipped weapon: the unarmed branch runs — pool flavor (the
        # potless fallback here), not the armed "You hit" line.
        out_hits = [t for _, t, c in player_msgs if c == 'combat-hit-out']
        self.assertTrue(out_hits)
        self.assertTrue(out_hits[0].startswith('You strike'))
        self.assertRegex(out_hits[0], r'for \d+ damage\.')
