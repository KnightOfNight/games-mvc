"""v24.19 brief 1 (#218): zombie combat session reaping.

CombatSession.npcs is M2M — one NpcInstance can belong to multiple
players' sessions. Pins the two-part fix: the kill path removes a dead
NPC from EVERY active session holding it (closing bystander sessions
left with no living NPCs, refocusing ones that retain some), and the
engine loop's self-heal closes any active zero-living-NPC session before
update_session_tick runs — so a zombie never refreshes its own
last_tick_at and the stale sweep stays live as the backstop.
"""
import asyncio
from datetime import timedelta
from unittest import mock

from django.test import TransactionTestCase
from django.utils import timezone

from apps.shyland.models import (
    CombatAction, CombatSession, COMBAT_ROUND_TICKS, NpcInstance,
)

from .test_combat_state import (
    make_character, make_npc, make_npc_definition, make_world,
)


def make_engine():
    """Engine harness (the test_combat_state pattern): a real Command
    with the transport stubbed to recording lists."""
    from apps.shyland.management.commands.run_tick_engine import Command
    cmd = Command()
    cmd.broadcasts = []
    cmd.player_sends = []

    async def record_broadcast(room_id, text, category='room',
                               exclude_pk=None, exclude_pks=None):
        cmd.broadcasts.append((room_id, text, category))

    async def record_send(character_pk, text, category, status,
                          event=None, fight=None):
        cmd.player_sends.append((character_pk, text, category, status, fight))

    async def all_online(pks):
        return set(pks)

    cmd.broadcast_to_room = record_broadcast
    cmd.send_to_player = record_send
    cmd._online_character_pks = all_online
    return cmd


def make_session(character, npcs, room, tick_counter=0, focus=None):
    session = CombatSession.objects.create(
        room=room, first_attacker='character',
        tick_counter=tick_counter, last_tick_at=timezone.now(),
        focus_npc=focus,
    )
    session.characters.add(character)
    for npc in npcs:
        session.npcs.add(npc)
    return session


class ZombieSessionTestCase(TransactionTestCase):
    """Shared drivers. TransactionTestCase: the engine's
    database_sync_to_async helpers run on their own connection."""

    def run_combat_tick(self, tick_number=1, force_hits=False):
        cmd = make_engine()
        if force_hits:
            # Deterministic kills: every swing lands plain (never a miss,
            # never a crit); a 1-hp NPC dies to any landed hit.
            with mock.patch('apps.shyland.combat_utils.resolve_hit_detailed',
                            return_value=('hit', {})):
                asyncio.run(cmd.process_combat(tick_number))
        else:
            asyncio.run(cmd.process_combat(tick_number))
        return cmd

    def sends_to(self, cmd, character_pk):
        return [s for s in cmd.player_sends if s[0] == character_pk]

    def texts_to(self, cmd, character_pk):
        return [(text, category) for _, text, category, _, _
                in self.sends_to(cmd, character_pk) if text]

    def queue_kill_round(self, character, session, npc):
        """Arm a session so the NEXT engine tick is its round boundary,
        with the character's attack on npc queued."""
        session.tick_counter = COMBAT_ROUND_TICKS - 1
        session.save(update_fields=['tick_counter'])
        CombatAction.objects.create(
            combat_session=session, character=character,
            action_type=CombatAction.ACTION_ATTACK, target_npc=npc,
        )


class CrossSessionKillTests(ZombieSessionTestCase):
    """Part A: the kill path is M2M-wide."""

    def setUp(self):
        self.zone, self.room = make_world('zk')
        self.char_a = make_character('zk_a', self.room)
        self.char_b = make_character('zk_b', self.room)
        self.definition = make_npc_definition('zk')

    def test_cross_session_kill_closes_the_bystander(self):
        # The headline fix: A and B each in their own session, both
        # holding the same single NPC; A's kill must end B's combat in
        # the same round — B was the player stuck behind the in-combat
        # gate, loot refused, in the live forensics.
        npc = make_npc(self.definition, self.room, hp=1)
        session_a = make_session(self.char_a, [npc], self.room)
        session_b = make_session(self.char_b, [npc], self.room)
        self.queue_kill_round(self.char_a, session_a, npc)

        cmd = self.run_combat_tick(force_hits=True)

        session_a.refresh_from_db()
        session_b.refresh_from_db()
        self.assertFalse(session_a.is_active)
        self.assertFalse(session_b.is_active)
        self.assertEqual(session_a.npcs.count(), 0)
        self.assertEqual(session_b.npcs.count(), 0)
        self.assertIn(("Combat has ended.", 'reward'),
                      self.texts_to(cmd, self.char_b.pk))
        # The loot gate's own predicate: B is out of combat.
        self.assertFalse(self.char_b.combat_sessions.filter(
            is_active=True).exists())
        # B's pane clears: a fight payload with active False was sent.
        b_fights = [f for _, _, _, _, f in self.sends_to(cmd, self.char_b.pk)
                    if f is not None]
        self.assertTrue(any(not f['active'] for f in b_fights))

    def test_cross_session_focus_reassignment(self):
        # B's session holds the shared NPC as focus plus a second living
        # NPC of its own: A's kill refocuses B aloud, never closes B.
        shared = make_npc(self.definition, self.room, hp=1)
        own = make_npc(self.definition, self.room, hp=20)
        session_a = make_session(self.char_a, [shared], self.room)
        session_b = make_session(self.char_b, [shared, own], self.room,
                                 focus=shared)
        self.queue_kill_round(self.char_a, session_a, shared)

        cmd = self.run_combat_tick(force_hits=True)

        session_b.refresh_from_db()
        self.assertTrue(session_b.is_active)
        self.assertEqual(session_b.focus_npc_id, own.pk)
        self.assertEqual([n.pk for n in session_b.npcs.all()], [own.pk])
        self.assertIn(("You turn your attacks on the cave spider.", 'combat'),
                      self.texts_to(cmd, self.char_b.pk))
        self.assertNotIn(("Combat has ended.", 'reward'),
                         self.texts_to(cmd, self.char_b.pk))


class SelfHealTests(ZombieSessionTestCase):
    """Part B: the loop-head self-heal, placed before the tick update."""

    def setUp(self):
        self.zone, self.room = make_world('zh')
        self.char = make_character('zh', self.room)
        self.definition = make_npc_definition('zh')

    def test_self_heal_closes_zombie_with_dead_row_attached(self):
        # The live forensic signature: an active session with one dead
        # NPC row attached. It must close on the next engine pass — and
        # its last_tick_at must NOT refresh (the no-refresh assertion is
        # what pins the stale sweep's restoration).
        npc = make_npc(self.definition, self.room, hp=20)
        NpcInstance.objects.filter(pk=npc.pk).update(
            is_alive=False, vitality_current=0)
        npc.refresh_from_db()
        session = make_session(self.char, [npc], self.room)
        stamp = timezone.now() - timedelta(seconds=5)
        CombatSession.objects.filter(pk=session.pk).update(last_tick_at=stamp)

        cmd = self.run_combat_tick()

        session.refresh_from_db()
        self.assertFalse(session.is_active)
        self.assertIsNone(session.focus_npc_id)
        self.assertEqual(session.npcs.count(), 0)
        self.assertEqual(session.last_tick_at, stamp)
        self.assertIn(("Combat has ended.", 'reward'),
                      self.texts_to(cmd, self.char.pk))

    def test_self_heal_closes_session_with_zero_npc_rows(self):
        session = make_session(self.char, [], self.room)
        stamp = timezone.now() - timedelta(seconds=5)
        CombatSession.objects.filter(pk=session.pk).update(last_tick_at=stamp)

        cmd = self.run_combat_tick()

        session.refresh_from_db()
        self.assertFalse(session.is_active)
        self.assertEqual(session.last_tick_at, stamp)
        self.assertIn(("Combat has ended.", 'reward'),
                      self.texts_to(cmd, self.char.pk))


class DeadNpcNeverRestoredTests(ZombieSessionTestCase):
    """Ruling 4: dead NPCs are never restored by any close path
    (release_session_npcs filters is_alive=True)."""

    def setUp(self):
        self.zone, self.room = make_world('zd')
        self.char_a = make_character('zd_a', self.room)
        self.char_b = make_character('zd_b', self.room)
        self.definition = make_npc_definition('zd')

    def test_dead_npc_stays_dead_through_both_close_paths(self):
        # Close path 1 — the cross-session kill (Part A).
        npc = make_npc(self.definition, self.room, hp=1)
        session_a = make_session(self.char_a, [npc], self.room)
        make_session(self.char_b, [npc], self.room)
        self.queue_kill_round(self.char_a, session_a, npc)
        self.run_combat_tick(force_hits=True)

        npc.refresh_from_db()
        self.assertFalse(npc.is_alive)
        self.assertEqual(npc.vitality_current, 0)

        # Close path 2 — the loop-head self-heal (Part B), on a fresh
        # manufactured zombie.
        npc2 = make_npc(self.definition, self.room, hp=20)
        NpcInstance.objects.filter(pk=npc2.pk).update(
            is_alive=False, vitality_current=0)
        npc2.refresh_from_db()
        make_session(self.char_b, [npc2], self.room)
        self.run_combat_tick()

        npc2.refresh_from_db()
        self.assertFalse(npc2.is_alive)
        self.assertEqual(npc2.vitality_current, 0)


class SharedLivingNpcGuardTests(ZombieSessionTestCase):
    """Regression on the v23 #25 multiplayer guard, pinned against this
    brief's new close paths: a living NPC in two active sessions keeps
    its current (damaged) vitality when another session closes in the
    same round."""

    def setUp(self):
        self.zone, self.room = make_world('zg')
        self.char_a = make_character('zg_a', self.room)
        self.char_b = make_character('zg_b', self.room)
        self.char_c = make_character('zg_c', self.room)
        self.definition = make_npc_definition('zg')

    def test_living_shared_npc_never_snaps_to_full(self):
        # Shared kill target in A's and B's sessions; a second NPC,
        # living and damaged, shared between B's and C's sessions. A's
        # kill closes A's session and refocuses B's — the damaged NPC,
        # still being fought in two active sessions, must keep its
        # damaged vitality through the round.
        target = make_npc(self.definition, self.room, hp=1)
        damaged = make_npc(self.definition, self.room, hp=20)
        NpcInstance.objects.filter(pk=damaged.pk).update(vitality_current=7)
        damaged.refresh_from_db()

        session_a = make_session(self.char_a, [target], self.room)
        session_b = make_session(self.char_b, [target, damaged], self.room,
                                 focus=target)
        session_c = make_session(self.char_c, [damaged], self.room)
        self.queue_kill_round(self.char_a, session_a, target)

        self.run_combat_tick(force_hits=True)

        session_a.refresh_from_db()
        session_b.refresh_from_db()
        session_c.refresh_from_db()
        self.assertFalse(session_a.is_active)
        self.assertTrue(session_b.is_active)
        self.assertTrue(session_c.is_active)

        damaged.refresh_from_db()
        self.assertTrue(damaged.is_alive)
        self.assertEqual(damaged.vitality_current, 7)
