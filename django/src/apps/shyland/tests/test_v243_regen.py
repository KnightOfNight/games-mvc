"""v24.3 Brief 1 (#165): the proportional regen law.

Out-of-combat regen rate = bar_max / CONSTANT points per second, so a
full refill from zero takes the constant's number of seconds at every
level. Vitality uses the per-tick form (ceil(max / VITALITY_REGEN_SECS)
per tick); Longevity uses the interval form (one point every
ceil(LONGEVITY_REGEN_SECS / max) ticks, keyed off tick_number) because
its max sits far below its constant and the per-tick ceil would always
be 1 (the ceil trap). These tests drive Phase 4 of process_effects
directly in async context (the test_tick_expiry engine-harness style)
and pin the law, the clamp, the exclusions, and regen silence.
"""

import math

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase

from apps.shyland.models import (
    Character, CombatSession, VITALITY_REGEN_SECS, LONGEVITY_REGEN_SECS,
)

from .test_command_revamp import make_character, make_world


def run_regen_engine():
    """Engine harness recording every send, status pushes included."""
    from apps.shyland.management.commands.run_tick_engine import Command
    cmd = Command()
    sent = []

    async def record_send(character_pk, text, category, status,
                          event=None, fight=None):
        sent.append((character_pk, text, category, status))

    async def record_broadcast(room_id, text, category='room',
                               exclude_pk=None, exclude_pks=None):
        pass
    cmd.send_to_player = record_send
    cmd.broadcast_to_room = record_broadcast
    return cmd, sent


def set_bars(char, **fields):
    Character.objects.filter(pk=char.pk).update(**fields)


def get_bars(char):
    c = Character.objects.get(pk=char.pk)
    return c.vitality_current, c.longevity_current


class VitalityRegenTests(TransactionTestCase):

    async def test_vitality_rate_is_proportional_to_max(self):
        def setup():
            zone, room = make_world('vrA')
            char = make_character('vrA', room)
            set_bars(char, vitality_max=718, vitality_current=100,
                     longevity_max=274, longevity_current=274)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(1)

        vit, lon = await sync_to_async(get_bars)(char)
        # ceil(718 / 120) = 6 per tick, regardless of the deficit's size.
        self.assertEqual(vit, 100 + math.ceil(718 / VITALITY_REGEN_SECS))
        self.assertEqual(vit, 106)

    async def test_vitality_clamps_at_max(self):
        def setup():
            zone, room = make_world('vrB')
            char = make_character('vrB', room)
            set_bars(char, vitality_max=718, vitality_current=717,
                     longevity_max=274, longevity_current=274)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(1)

        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(vit, 718)   # +1, clamped — never overshoots

    async def test_vitality_law_full_refill_in_120_ticks(self):
        def setup():
            zone, room = make_world('vrC')
            char = make_character('vrC', room)
            set_bars(char, vitality_max=718, vitality_current=0,
                     longevity_max=274, longevity_current=274)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        ticks = 0
        vit = 0
        while vit < 718 and ticks < 200:
            ticks += 1
            await cmd.process_effects(ticks)
            vit, lon = await sync_to_async(get_bars)(char)
        # The law: full from zero in ceil(718 / 6) = 120 ticks — the
        # VITALITY_REGEN_SECS promise within one tick.
        self.assertEqual(ticks, math.ceil(718 / math.ceil(718 / VITALITY_REGEN_SECS)))
        self.assertEqual(ticks, 120)


class LongevityRegenTests(TransactionTestCase):

    async def test_longevity_heals_one_on_interval_ticks_only(self):
        def setup():
            zone, room = make_world('lrA')
            char = make_character('lrA', room)
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=274, longevity_current=100)
            return char
        char = await sync_to_async(setup)()

        interval = math.ceil(LONGEVITY_REGEN_SECS / 274)
        self.assertEqual(interval, 14)

        cmd, sent = run_regen_engine()
        await cmd.process_effects(interval * 2)      # 28 % 14 == 0
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 101)

        await cmd.process_effects(interval * 2 + 1)  # adjacent tick
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 101)                   # nothing this tick

    async def test_longevity_clamps_at_max(self):
        def setup():
            zone, room = make_world('lrB')
            char = make_character('lrB', room)
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=274, longevity_current=273)
            return char
        char = await sync_to_async(setup)()

        interval = math.ceil(LONGEVITY_REGEN_SECS / 274)
        cmd, sent = run_regen_engine()
        await cmd.process_effects(interval)
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 274)

        # A further interval tick at max changes nothing.
        await cmd.process_effects(interval * 3)
        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual(lon, 274)

    def test_longevity_law_arithmetic(self):
        # The law asserted via the interval, not a 3836-iteration loop:
        # at a 274 bar the interval is ceil(3600/274) = 14 ticks/point,
        # so full recovery from zero spans 274 × 14 = 3836 ticks (~64
        # min) — the LONGEVITY_REGEN_SECS promise within one interval.
        interval = math.ceil(LONGEVITY_REGEN_SECS / 274)
        self.assertEqual(interval, 14)
        total_ticks = 274 * interval
        self.assertEqual(total_ticks, 3836)
        self.assertGreaterEqual(total_ticks, LONGEVITY_REGEN_SECS)
        self.assertLess(total_ticks, LONGEVITY_REGEN_SECS + 274)


class RegenExclusionTests(TransactionTestCase):

    async def test_active_combat_excludes_both_bars(self):
        def setup():
            zone, room = make_world('reA')
            char = make_character('reA', room)
            set_bars(char, vitality_max=718, vitality_current=100,
                     longevity_max=274, longevity_current=100)
            session = CombatSession.objects.create(room=room, is_active=True)
            session.characters.add(char)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        interval = math.ceil(LONGEVITY_REGEN_SECS / 274)
        await cmd.process_effects(interval * 2)      # an interval tick, too

        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual((vit, lon), (100, 100))

    async def test_dying_excludes_both_bars(self):
        def setup():
            zone, room = make_world('reB')
            char = make_character('reB', room)
            set_bars(char, vitality_max=718, vitality_current=0,
                     longevity_max=274, longevity_current=100,
                     is_dying=True)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        interval = math.ceil(LONGEVITY_REGEN_SECS / 274)
        await cmd.process_effects(interval * 2)

        vit, lon = await sync_to_async(get_bars)(char)
        self.assertEqual((vit, lon), (0, 100))


class RegenSilenceTests(TransactionTestCase):

    async def test_regen_tick_pushes_status_only_no_output(self):
        def setup():
            zone, room = make_world('rsA')
            char = make_character('rsA', room)
            set_bars(char, vitality_max=718, vitality_current=100,
                     longevity_max=274, longevity_current=274)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_regen_engine()
        await cmd.process_effects(1)

        mine = [s for s in sent if s[0] == char.pk]
        # No output message ever — the status push is the only signal.
        self.assertEqual([s for s in mine if s[1]], [])
        statuses = [s for s in mine if s[2] == 'status']
        self.assertEqual(len(statuses), 1)
        self.assertIsNotNone(statuses[0][3])

    async def test_no_field_change_means_no_push_at_all(self):
        def setup():
            zone, room = make_world('rsB')
            char = make_character('rsB', room)
            # Longevity-only deficit: on a non-interval tick nothing
            # changes, so the changed_fields gate must send nothing.
            set_bars(char, vitality_max=718, vitality_current=718,
                     longevity_max=274, longevity_current=100)
            return char
        char = await sync_to_async(setup)()

        interval = math.ceil(LONGEVITY_REGEN_SECS / 274)
        cmd, sent = run_regen_engine()
        await cmd.process_effects(interval * 2 + 1)  # not an interval tick

        self.assertEqual([s for s in sent if s[0] == char.pk], [])
