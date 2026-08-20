"""v23 brief 3 (#141): level-up message split + stats hint removal.

A level-up emits two reward messages (level/bars, then unspent points
with the short spend hint), neither with the *** prefix; the stats
report keeps the Unspent stat points count but drops the syntax hint
(discoverability lives in help and SPEND_USAGE)."""

from asgiref.sync import sync_to_async
from unittest import mock

from django.test import TransactionTestCase

from apps.shyland.combat_utils import xp_for_next_level
from apps.shyland.models import Character

from .test_command_revamp import (
    make_character, make_stub_consumer, make_world,
)
from .test_gear_combat import make_combat_world, run_engine_round


class LevelUpMessageTests(TransactionTestCase):

    async def test_level_up_emits_two_reward_messages_no_prefix(self):
        def setup():
            char, npc = make_combat_world('luA', npc_vitality=1)
            # One point below the level-2 threshold with prior unspent
            # points banked: any kill XP tips the level.
            Character.objects.filter(pk=char.pk).update(
                xp=xp_for_next_level(1) - 1, unspent_stat_points=3)
            return char, npc
        char, npc = await sync_to_async(setup)()

        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit_detailed',
                        return_value=('hit', {})):
            await cmd.process_combat(1)

        rewards = [t for pk, t, c in player_msgs
                   if pk == char.pk and c == 'reward'
                   and not t.startswith('You have slain')
                   and t != 'Combat has ended.']
        self.assertEqual(len(rewards), 2)
        self.assertTrue(rewards[0].startswith('You have reached level 2!'))
        self.assertIn('Your Vitality is now', rewards[0])
        self.assertNotIn('unspent', rewards[0])

        def pts():
            return Character.objects.get(pk=char.pk).unspent_stat_points
        accumulated = await sync_to_async(pts)()
        # 3 banked + STAT_POINTS_PER_LEVEL — the accumulated count.
        self.assertEqual(
            rewards[1],
            f"You have {accumulated} unspent stat points. "
            "Type 'spend' to allocate them.")
        for t in rewards:
            self.assertFalse(t.startswith('***'))


class StatsHintRemovalTests(TransactionTestCase):

    async def test_stats_shows_count_but_no_hint_line(self):
        zone, room = await sync_to_async(make_world)('shA')

        def setup():
            char = make_character('shA', room)
            Character.objects.filter(pk=char.pk).update(unspent_stat_points=2)
            return Character.objects.select_related(
                'user', 'origin', 'archetype',
                'current_room__zone', 'current_room__area',
            ).get(pk=char.pk)
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()

        report = next(m for m in sent if m.get('category') == 'report'
                      and 'lines' in m)
        texts = [(e.get('k', '') or '') + (e.get('v', '') or '')
                 for e in report['lines'] if 'segs' not in e]
        self.assertTrue(
            any('Unspent stat points: 2' in t for t in texts))
        self.assertFalse(
            any('to allocate. (e.g.' in t for t in texts))
