"""V24.17 brief 1 (#105): NPC DEX curve rounding parity.

The curve's growth term is floored (18 + floor(2.5 x (L - 1))),
mirroring the reference player's floor-share DEX accrual, so the
blessed at-level hit targets (55% normal / 45% elite / 45% boss) are
exact at every level of every band. Banker's round() drifted -5% hit
at the .5-up levels (L4/L8 per band): elite L4 28 -> 27, L8 38 -> 37.
STR/PER/INT growth deliberately keeps its Amendment-1 round() and is
not pinned here.
"""
import math

from django.test import TestCase

from apps.shyland.combat_utils import (
    NPC_TIER_OFFSET, TO_HIT_DEFENSE_BASE, get_npc_stats,
)
from apps.shyland.models import NpcDefinition, NpcInstance

TIERS = ('normal', 'elite', 'boss')


def make_npc(scaling_factor, combat_tier, mk_tier):
    """Unsaved definition/instance pair — get_npc_stats reads only
    definition fields, mk_tier, and vitality_current."""
    defn = NpcDefinition(
        name='parity beetle', slug='parity-beetle',
        description='A test enemy.', genre_tag='fantasy',
        indefinite_article='a', is_aggressive=False,
        combat_tier=combat_tier, scaling_factor=scaling_factor,
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    return NpcInstance(
        definition=defn, mk_tier=mk_tier,
        vitality_current=10, vitality_max=10,
    )


def attainable_primary(level):
    """The reference player's at-level primary: floor-share of 2.5
    DEX per level (5 stat points split across two primaries)."""
    return 18 + math.floor(2.5 * (level - 1))


class DexCurveLawTests(TestCase):
    """The curve law across every band, within-band level, and tier."""

    def test_curve_law(self):
        for mk_tier in (1, 2, 3):
            for sf in range(1, 11):
                level = sf + 10 * (mk_tier - 1)
                for tier in TIERS:
                    npc = make_npc(float(sf), tier, mk_tier)
                    self.assertEqual(
                        get_npc_stats(npc)['dex'],
                        18 + math.floor(2.5 * (level - 1)) + NPC_TIER_OFFSET[tier],
                        f'mk_tier={mk_tier} sf={sf} tier={tier}',
                    )


class PlayerParityTests(TestCase):
    """Normal-tier NPC DEX equals the reference player's attainable
    primary at every effective level."""

    def test_player_parity(self):
        for level in range(1, 31):
            mk_tier = (level - 1) // 10 + 1
            sf = level - 10 * (mk_tier - 1)
            npc = make_npc(float(sf), 'normal', mk_tier)
            self.assertEqual(
                get_npc_stats(npc)['dex'], attainable_primary(level),
                f'level={level}',
            )


class BlessedTargetsTests(TestCase):
    """With player DEX = the attainable primary, the to-hit threshold
    yields exactly 55% / 45% / 45% at every level and tier."""

    BLESSED = {'normal': (10, 11), 'elite': (12, 9), 'boss': (12, 9)}

    def test_blessed_targets_exact(self):
        for level in range(1, 31):
            mk_tier = (level - 1) // 10 + 1
            sf = level - 10 * (mk_tier - 1)
            player_dex = attainable_primary(level)
            for tier in TIERS:
                npc = make_npc(float(sf), tier, mk_tier)
                threshold = (TO_HIT_DEFENSE_BASE
                             + get_npc_stats(npc)['dex'] - player_dex)
                expected_threshold, expected_faces = self.BLESSED[tier]
                self.assertEqual(threshold, expected_threshold,
                                 f'level={level} tier={tier}')
                self.assertEqual(21 - threshold, expected_faces,
                                 f'level={level} tier={tier}')


class SentinelTests(TestCase):
    """The two drift levels move; the aligned levels are byte-identical."""

    def test_elite_l4_sentinel(self):
        # Banker's round(25.5) = 26 gave 28; floor gives 27.
        npc = make_npc(4.0, 'elite', 1)
        self.assertEqual(get_npc_stats(npc)['dex'], 27)

    def test_elite_l8_sentinel(self):
        # Banker's round(35.5) = 36 gave 38; floor gives 37.
        npc = make_npc(8.0, 'elite', 1)
        self.assertEqual(get_npc_stats(npc)['dex'], 37)

    def test_aligned_levels_unchanged(self):
        # The levels banker's already got right: surgical-fix pins.
        for sf, expected in ((2.0, 20), (6.0, 30), (10.0, 40)):
            npc = make_npc(sf, 'normal', 1)
            self.assertEqual(get_npc_stats(npc)['dex'], expected, f'sf={sf}')
