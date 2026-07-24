"""v23 brief 1 (#143, #25): flee & disengagement.

The flee contest's NPC side reads effective PER via
flee_contest_npc_side() — the same get_npc_stats() read every other
combat contest uses (semantics pinned, not snapshot numbers). The
session-end-without-death reset: release_session_npcs() restores
surviving NPCs to full vitality on last-active-session exit, with the
multiplayer guard keeping shared instances live."""

from django.test import SimpleTestCase, TestCase

from apps.shyland.combat_utils import (
    flee_contest_npc_side, get_npc_stats, release_session_npcs,
)
from apps.shyland.models import CombatSession, NpcDefinition, NpcInstance
from apps.shyland.tests.test_command_revamp import make_character, make_world


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


def make_npc_instance(prefix, room, vitality_current, vitality_max=20,
                      is_alive=True):
    defn = NpcDefinition.objects.create(
        name=f'{prefix} snarler', slug=f'{prefix}-snarler',
        description='x', genre_tag='fantasy',
        base_vitality=vitality_max, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    return NpcInstance.objects.create(
        definition=defn, current_room=room, spawn_room=room,
        vitality_current=vitality_current, vitality_max=vitality_max,
        is_alive=is_alive,
    )


class ReleaseSessionNpcsTests(TestCase):
    """#25: full reset on last-active-session exit; multiplayer guard;
    dead NPCs untouched; full-health no-op."""

    def _session(self, room, char, npc):
        session = CombatSession.objects.create(room=room)
        session.characters.add(char)
        session.npcs.add(npc)
        return session

    def _end(self, session):
        # Callers mark-and-save first (belt and suspenders per the
        # ruling notes), then route through the helper.
        session.is_active = False
        session.save(update_fields=['is_active'])
        release_session_npcs(session)

    def test_reset_on_last_session_exit(self):
        zone, room = make_world('flA')
        char = make_character('flA', room)
        npc = make_npc_instance('flA', room, vitality_current=10)
        session = self._session(room, char, npc)

        self._end(session)

        npc.refresh_from_db()
        self.assertEqual(npc.vitality_current, npc.vitality_max)
        self.assertEqual(session.npcs.count(), 0)

    def test_multiplayer_guard(self):
        zone, room = make_world('flB')
        char_a = make_character('flB', room)
        char_b = make_character('flB2', room)
        npc = make_npc_instance('flB', room, vitality_current=7)
        session_a = self._session(room, char_a, npc)
        session_b = self._session(room, char_b, npc)

        self._end(session_a)
        npc.refresh_from_db()
        self.assertEqual(npc.vitality_current, 7)   # live state — no snap
        self.assertEqual(session_a.npcs.count(), 0)
        self.assertEqual(session_b.npcs.count(), 1)

        self._end(session_b)
        npc.refresh_from_db()
        self.assertEqual(npc.vitality_current, npc.vitality_max)
        self.assertEqual(session_b.npcs.count(), 0)

    def test_dead_npcs_untouched(self):
        zone, room = make_world('flC')
        char = make_character('flC', room)
        npc = make_npc_instance('flC', room, vitality_current=0,
                                is_alive=False)
        session = self._session(room, char, npc)

        self._end(session)

        npc.refresh_from_db()
        self.assertEqual(npc.vitality_current, 0)
        self.assertEqual(session.npcs.count(), 0)

    def test_full_health_noop(self):
        zone, room = make_world('flD')
        char = make_character('flD', room)
        npc = make_npc_instance('flD', room, vitality_current=20)
        session = self._session(room, char, npc)

        self._end(session)

        npc.refresh_from_db()
        self.assertEqual(npc.vitality_current, npc.vitality_max)
        self.assertEqual(session.npcs.count(), 0)
