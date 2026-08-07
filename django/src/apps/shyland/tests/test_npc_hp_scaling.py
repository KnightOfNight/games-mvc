"""V24.13 brief 1 (#104): NPC HP scales with Mk tier at spawn time.

Covers the npc_max_vitality helper (linear per-band lift, rounded
half-up — the 150 -> 263 case is the banker's-rounding sentinel that
fails under built-in round(), cf. #105), the Mk 1 identity invariant
(zero change to any shipped spawn), and the respawn sweep persisting
the lifted value to vitality_current/vitality_max at the single
NpcInstance creation site.
"""
import asyncio

from django.test import TestCase, TransactionTestCase

from apps.shyland.combat_utils import npc_max_vitality
from apps.shyland.models import (
    NpcDefinition, NpcInstance, Room, RoomSpawn, Zone,
)


def make_world(prefix):
    zone = Zone.objects.create(
        name=f'{prefix} Zone', slug=f'{prefix}-zone',
        genre_tone='Test', danger_level='beginner',
        description='A test zone.',
    )
    room = Room.objects.create(
        zone=zone, name=f'{prefix} Room',
        description='Long.', brief_description='Brief.',
        coord_x=0, coord_y=0,
    )
    return zone, room


def make_npc_definition(prefix, base_vitality=40):
    return NpcDefinition.objects.create(
        name='cave beetle', slug=f'{prefix}-cave-beetle',
        description='A test enemy.', genre_tag='fantasy',
        indefinite_article='a',
        is_aggressive=False,
        base_vitality=base_vitality, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )


class NpcMaxVitalityTests(TestCase):
    """Helper unit cases — expected values are binding (brief §4 table)."""

    CASES = [
        # (base_vitality, mk_tier, expected)
        (25,  1, 25),
        (40,  1, 40),
        (150, 1, 150),
        (999, 1, 999),
        (25,  2, 44),
        (40,  2, 70),
        (150, 2, 263),   # banker's-rounding sentinel: round(262.5) == 262
        (240, 2, 420),
        (260, 2, 455),
        (75,  3, 188),
    ]

    def test_table_cases(self):
        for base, tier, expected in self.CASES:
            defn = NpcDefinition(base_vitality=base)
            self.assertEqual(
                npc_max_vitality(defn, tier), expected,
                f'base_vitality={base} mk_tier={tier}',
            )

    def test_mk1_identity_invariant(self):
        # Mk 1 multiplies by exactly 1 — no shipped spawn number moves.
        for base in range(1, 1001):
            defn = NpcDefinition(base_vitality=base)
            self.assertEqual(npc_max_vitality(defn, 1), base)


class RespawnSweepHpTests(TransactionTestCase):
    """The respawn sweep persists the lifted HP to both instance fields."""

    def _command(self):
        from apps.shyland.management.commands.run_tick_engine import Command
        return Command()

    def _spawn(self, definition, room, mk_tier):
        return RoomSpawn.objects.create(
            room=room, npc_definition=definition, mk_tier=mk_tier,
            count=1, is_active=True,
        )

    def test_mk2_spawn_carries_lifted_hp(self):
        zone, room = make_world('hp2')
        definition = make_npc_definition('hp2', base_vitality=40)
        self._spawn(definition, room, mk_tier=2)

        asyncio.run(self._command().process_npc_respawn())

        npc = NpcInstance.objects.get(definition=definition)
        self.assertEqual(npc.vitality_current, 70)
        self.assertEqual(npc.vitality_max, 70)

    def test_mk1_spawn_unchanged(self):
        # Live-content invariance at the integration layer.
        zone, room = make_world('hp1')
        definition = make_npc_definition('hp1', base_vitality=40)
        self._spawn(definition, room, mk_tier=1)

        asyncio.run(self._command().process_npc_respawn())

        npc = NpcInstance.objects.get(definition=definition)
        self.assertEqual(npc.vitality_current, 40)
        self.assertEqual(npc.vitality_max, 40)
