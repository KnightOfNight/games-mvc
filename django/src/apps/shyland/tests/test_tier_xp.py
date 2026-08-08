"""V24.15 brief 1 (#26): combat-tier kill-XP multiplier — the doubling
ladder.

Covers the NPC_TIER_XP_MULT ladder shape (exactly the ruled table, every
COMBAT_TIER_CHOICES key present so a future sixth tier fails loudly
instead of silently paying x1, each rung 2x the previous in choices
order), the sentinel/composition table for xp_for_kill (the multiplier
applies to the base BEFORE the v18 outleveled decay — the Matron
sentinel moves 30 -> 240), and the unknown-tier x1 default.
"""
from types import SimpleNamespace

from django.test import TestCase

from apps.shyland.combat_utils import NPC_TIER_XP_MULT, xp_for_kill
from apps.shyland.models import NpcDefinition


def make_npc_stub(combat_tier, mk_tier, scaling_factor):
    definition = SimpleNamespace(combat_tier=combat_tier,
                                 scaling_factor=scaling_factor)
    return SimpleNamespace(definition=definition, mk_tier=mk_tier)


def make_character_stub(level):
    return SimpleNamespace(level=level)


class TierXpLadderTests(TestCase):
    """The ladder is exactly the ruled table, complete over the tier choices."""

    def test_ladder_matches_ruled_table_exactly(self):
        self.assertEqual(
            NPC_TIER_XP_MULT,
            {'normal': 1, 'elite': 2, 'champion': 4, 'boss': 8, 'world_boss': 16},
        )

    def test_every_combat_tier_choice_has_a_rung(self):
        # A future sixth tier must fail here loudly, not silently pay x1.
        for key, _label in NpcDefinition.COMBAT_TIER_CHOICES:
            self.assertIn(key, NPC_TIER_XP_MULT)
        self.assertEqual(
            set(NPC_TIER_XP_MULT),
            {key for key, _label in NpcDefinition.COMBAT_TIER_CHOICES},
        )

    def test_each_rung_doubles_the_previous_in_choices_order(self):
        keys = [key for key, _label in NpcDefinition.COMBAT_TIER_CHOICES]
        for prev, cur in zip(keys, keys[1:]):
            self.assertEqual(NPC_TIER_XP_MULT[cur], NPC_TIER_XP_MULT[prev] * 2)
        self.assertTrue(all(isinstance(v, int) for v in NPC_TIER_XP_MULT.values()))


class TierXpCompositionTests(TestCase):
    """Sentinels: the tier multiplier composes before the outleveled decay."""

    # (combat_tier, mk_tier, scaling_factor, char level, expected XP, proves)
    SENTINELS = [
        ('normal',     1, 3.0,  3,  30, 'x1 unchanged'),
        ('elite',      1, 3.0,  3,  60, 'x2'),
        ('champion',   1, 3.0,  3, 120, 'x4'),
        ('boss',       1, 3.0,  3, 240, 'the Matron sentinel (was 30)'),
        ('world_boss', 1, 3.0,  3, 480, 'x16'),
        ('boss',       1, 3.0, 13,  96, 'decay after tier: 240 x 0.4'),
        ('boss',       1, 3.0, 30,  24, '10% floor of tier-multiplied base'),
        ('normal',     1, 0.5, 30,   1, 'absolute min 1 preserved'),
    ]

    def test_sentinels(self):
        for tier, mk, sf, level, expected, proves in self.SENTINELS:
            with self.subTest(tier=tier, level=level, proves=proves):
                npc = make_npc_stub(tier, mk, sf)
                char = make_character_stub(level)
                self.assertEqual(xp_for_kill(npc, char), expected)

    def test_unknown_tier_pays_x1(self):
        npc = make_npc_stub('ascended', 1, 3.0)
        char = make_character_stub(3)
        self.assertEqual(xp_for_kill(npc, char), 30)
