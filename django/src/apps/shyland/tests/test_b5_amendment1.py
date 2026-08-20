"""v22 Brief 5 Amendment 1 — Armor Visibility.

The stats-sheet Armor row (TAV + live mitigation percentage), the examine
contribution line (slot weight per Mk, worn share, broken confession),
and the incoming-hit (-N) parenthetical under the one-vocabulary rule:
the leading number moved the bar, the parenthetical is gear's share.
"""

import re

from asgiref.sync import sync_to_async
from unittest import mock

from django.test import TransactionTestCase

from apps.shyland.models import Character, ItemInstance

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world,
)
from .test_gear_combat import (
    equip_gear, make_combat_world, make_gear_def, run_engine_round,
)

# The eight armor-carrying slots with their v24.9 (#129) authored bases —
# the retired slot weights, now authored per definition (importing
# TotalArmorValueTests here would re-register its tests in this module's
# namespace).
FULL_SET_SLOTS = (('CHEST', 3.0), ('HEAD', 2.0), ('LEGS', 2.0),
                  ('OFF_HAND', 2.0), ('SHOULDERS', 1.0), ('HANDS', 1.0),
                  ('WAIST', 1.0), ('FEET', 1.0))


def full_common_mk1_set(prefix, char):
    items = {}
    for slot, base in FULL_SET_SLOTS:
        defn = make_gear_def(prefix, f'{prefix} {slot} piece',
                             item_type='armor', slot=slot, armor_base=base)
        items[slot] = equip_gear(defn, char, slot, mk=1)
    return items


class StatsArmorRowTests(TransactionTestCase):

    def _stat_lines(self, sent):
        for msg in sent:
            if msg.get('type') == 'output' and 'lines' in msg:
                return [line.get('v', '') for line in msg['lines'] if line]
        return []

    async def test_naked_armor_zero_no_parenthetical(self):
        def setup():
            zone, room = make_world('arA')
            return make_character('arA', room)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()
        lines = self._stat_lines(sent)
        self.assertIn('  Armor: 0', lines)
        for line in lines:
            self.assertNotIn('blocks', line)

    async def test_full_set_blocks_21_percent(self):
        def setup():
            zone, room = make_world('arB')
            char = make_character('arB', room)
            full_common_mk1_set('arB', char)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()
        self.assertIn('  Armor: 13 (blocks 21%)', self._stat_lines(sent))

    async def test_broken_chestpiece_lowers_both_numbers(self):
        def setup():
            zone, room = make_world('arC')
            char = make_character('arC', room)
            items = full_common_mk1_set('arC', char)
            items['CHEST'].is_broken = True
            items['CHEST'].save()
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()
        # TAV 10 -> round(1000/58) = 17.
        self.assertIn('  Armor: 10 (blocks 17%)', self._stat_lines(sent))


class ExamineArmorLineTests(TransactionTestCase):

    def test_unworn_piece_shows_weight_no_parenthetical(self):
        zone, room = make_world('exA')
        char = make_character('exA', room)
        defn = make_gear_def('exA', 'Leather Chestpiece',
                             item_type='armor', slot='CHEST',
                             armor_base=3.0)
        item = ItemInstance.objects.create(
            definition=defn, owner=char, mk_tier=1, rarity='common',
            is_identified=True)
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        armor_lines = [l for l in lines if l.strip().startswith('Armor:')]
        self.assertEqual(armor_lines, ['  Armor:      3 per Mk'])

    def test_equipped_piece_shows_worn_contribution(self):
        zone, room = make_world('exB')
        char = make_character('exB', room)
        defn = make_gear_def('exB', 'Leather Chestpiece',
                             item_type='armor', slot='CHEST',
                             armor_base=3.0)
        item = equip_gear(defn, char, 'CHEST', mk=1)
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertIn('  Armor:      3 per Mk (worn: 3)', lines)

    def test_broken_equipped_piece_confesses(self):
        zone, room = make_world('exC')
        char = make_character('exC', room)
        defn = make_gear_def('exC', 'Leather Chestpiece',
                             item_type='armor', slot='CHEST',
                             armor_base=3.0)
        item = equip_gear(defn, char, 'CHEST', mk=1, broken=True,
                          durability=0.0)
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertIn('  Armor:      3 per Mk (worn: 0 — broken)', lines)

    def test_non_armor_items_gain_no_line(self):
        zone, room = make_world('exD')
        char = make_character('exD', room)
        defn = make_item_def('exD', 'Plain Rock')
        item = make_owned_item(defn, char)
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertFalse([l for l in lines if 'Armor:' in l])

    def test_mk2_worn_contribution_scales(self):
        zone, room = make_world('exE')
        char = make_character('exE', room)
        defn = make_gear_def('exE', 'Sturdy Helm', item_type='armor',
                             slot='HEAD', armor_base=2.0)
        item = equip_gear(defn, char, 'HEAD', mk=2)
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertIn('  Armor:      2 per Mk (worn: 4)', lines)

    def test_zero_base_armor_item_shows_no_line(self):
        # v24.9 (#129): the display gate is the authored base, not the
        # item type — an armor-type item authoring 0 confesses nothing.
        zone, room = make_world('exF')
        char = make_character('exF', room)
        defn = make_gear_def('exF', 'Ceremonial Sash', item_type='armor',
                             slot='WAIST')
        item = equip_gear(defn, char, 'WAIST', mk=1)
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertFalse([l for l in lines if 'Armor:' in l])

    def test_non_armor_item_with_base_shows_the_line(self):
        # v24.9 (#129): no type gate — any definition authoring
        # protection confesses it.
        zone, room = make_world('exG')
        char = make_character('exG', room)
        defn = make_gear_def('exG', 'Warding Ring', item_type='accessory',
                             slot='RING', armor_base=1.0)
        item = equip_gear(defn, char, 'RING', mk=1)
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(item)
        self.assertIn('  Armor:      1 per Mk (worn: 1)', lines)


class IncomingLineTests(TransactionTestCase):
    """Amendment 2 rewrote these: the (-N) parenthetical is gone (it was
    Amendment 1 scaffolding). Incoming lines carry only the
    post-mitigation number (the bar delta) — armored and unarmored share
    the same form, the quiet-line law unconditional. Mitigation math is
    unchanged and still asserted through the bar delta."""

    def _in_lines(self, player_msgs, category='combat-hit-in'):
        return [t for _, t, c in player_msgs if c == category]

    async def test_unarmored_line_byte_identical(self):
        char, npc = await sync_to_async(make_combat_world)('ipA')
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit_detailed',
                        return_value=('hit', {})):
            await cmd.process_combat(1)
        in_hits = self._in_lines(player_msgs)
        self.assertTrue(in_hits)
        self.assertRegex(in_hits[0], r'for \d+ damage\.')
        self.assertNotIn('(-', in_hits[0])

    async def test_armored_leading_number_is_the_bar_delta_no_parenthetical(self):
        def setup():
            char, npc = make_combat_world('ipB', npc_str=20)
            full_common_mk1_set('ipB', char)
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit_detailed',
                        return_value=('hit', {})), \
             mock.patch('random.uniform', return_value=20.0):
            await cmd.process_combat(1)

        in_hits = self._in_lines(player_msgs)
        self.assertTrue(in_hits)
        self.assertNotIn('(-', in_hits[0])
        # raw 20, TAV 13: reduction round(20 x 13/61) = 4 -> landed 16 —
        # mitigation still applied, only silently.
        m = re.search(r'for (\d+) damage\.', in_hits[0])
        self.assertIsNotNone(m, in_hits[0])
        landed = int(m.group(1))
        self.assertEqual(landed, 16)

        def vit():
            return Character.objects.get(pk=char.pk).vitality_current
        self.assertEqual(await sync_to_async(vit)(), 100 - landed)

    async def test_armored_crit_plain_form(self):
        def setup():
            char, npc = make_combat_world('ipC', npc_str=20)
            full_common_mk1_set('ipC', char)
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit_detailed',
                        return_value=('critical', {})), \
             mock.patch('random.uniform', return_value=20.0):
            await cmd.process_combat(1)
        in_crits = self._in_lines(player_msgs, 'combat-crit-in')
        self.assertTrue(in_crits)
        # raw 30 (crit x1.5): reduction round(30 x 13/61) = 6 -> 24.
        self.assertRegex(in_crits[0], r'for a critical 24 damage!')
        self.assertNotIn('(-', in_crits[0])

    async def test_armored_graze_plain_form(self):
        def setup():
            char, npc = make_combat_world('ipD', npc_str=20)
            full_common_mk1_set('ipD', char)
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit_detailed',
                        return_value=('graze', {})), \
             mock.patch('random.uniform', return_value=20.0):
            await cmd.process_combat(1)
        in_hits = self._in_lines(player_msgs)
        self.assertTrue(in_hits)
        # raw 10 (graze x0.5): reduction round(10 x 13/61) = 2 -> 8.
        self.assertRegex(in_hits[0], r'for 8 damage\.')
        self.assertNotIn('(-', in_hits[0])

    async def test_floor_case_tav_1_plain_form(self):
        def setup():
            char, npc = make_combat_world('ipE', npc_str=2)
            defn = make_gear_def('ipE', 'Thin Charm')
            equip_gear(defn, char, 'WAIST', secondary=[
                {'stat': 'physical_resist', 'value': 1}])
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit_detailed',
                        return_value=('hit', {})), \
             mock.patch('random.uniform', return_value=2.0):
            await cmd.process_combat(1)
        in_hits = self._in_lines(player_msgs)
        self.assertTrue(in_hits)
        # raw 2, TAV 1: reduction max(1, round(2/49)) = 1 -> landed 1.
        self.assertRegex(in_hits[0], r'for 1 damage\.')
        self.assertNotIn('(-', in_hits[0])
