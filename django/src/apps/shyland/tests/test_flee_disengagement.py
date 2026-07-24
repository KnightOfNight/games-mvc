"""v23 brief 1 (#143, #25): flee & disengagement.

The flee contest's NPC side reads effective PER via
flee_contest_npc_side() — the same get_npc_stats() read every other
combat contest uses (semantics pinned, not snapshot numbers)."""

from django.test import SimpleTestCase

from apps.shyland.combat_utils import flee_contest_npc_side, get_npc_stats
from apps.shyland.models import NpcDefinition, NpcInstance


def mem_npc(base_per, scaling_factor, mk_tier, combat_tier='normal'):
    defn = NpcDefinition(
        name='mem snarler', slug='mem-snarler', description='x',
        genre_tag='fantasy', combat_tier=combat_tier,
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=base_per,
        scaling_factor=scaling_factor,
    )
    npc = NpcInstance(mk_tier=mk_tier, vitality_current=10, vitality_max=10)
    npc.definition = defn
    return npc


class FleeContestNpcSideTests(SimpleTestCase):
    """#143: the NPC side is the session mean of effective PER."""

    def test_session_mean_of_effective_per(self):
        npcs = [
            mem_npc(base_per=10, scaling_factor=6.0, mk_tier=1),
            mem_npc(base_per=14, scaling_factor=8.0, mk_tier=2,
                    combat_tier='elite'),
            mem_npc(base_per=8, scaling_factor=10.0, mk_tier=1,
                    combat_tier='boss'),
            mem_npc(base_per=12, scaling_factor=3.0, mk_tier=3),
        ]
        expected = sum(get_npc_stats(n)['per'] for n in npcs) / len(npcs)
        self.assertEqual(flee_contest_npc_side(npcs), expected)

    def test_single_npc_is_its_own_mean(self):
        npc = mem_npc(base_per=10, scaling_factor=6.0, mk_tier=1)
        self.assertEqual(
            flee_contest_npc_side([npc]), get_npc_stats(npc)['per'])

    def test_issue_table_anchor_l6_normal(self):
        # #143's authoritative table: an L6 normal at Mk 1 with
        # base_per=10 has effective PER 22 — 10 + round(2.5 × 5), with
        # Python banker's rounding giving round(12.5) == 12.
        npc = mem_npc(base_per=10, scaling_factor=6.0, mk_tier=1)
        self.assertEqual(get_npc_stats(npc)['per'], 22)
