"""v22 brief 2 amendment 1 (#123, #124, #120): listing columns, color
re-tags, the version constant, and the Bound/Unbound vocabulary law."""

import asyncio
from datetime import timedelta
from unittest import mock

from asgiref.sync import sync_to_async
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.version import SHYLAND_VERSION
from apps.shyland.models import (
    Character, CombatSession, Corpse, ItemDefinition, ItemInstance,
    NpcDefinition, NpcInstance,
)
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, make_vendor, make_world, outputs,
)


def make_def(prefix, name, item_type='material', valid_slots=None,
             base_value=1, takes_durability=False):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type=item_type, genre_tag='fantasy',
        valid_slots=valid_slots or [],
        scaling_base=0.0, scaling_factor=0.0, base_value=base_value,
        takes_durability_loss=takes_durability,
    )


def line_texts(sent):
    """Flatten a report message's lines to plain strings."""
    report = next(m for m in sent if m.get('category') == 'report'
                  and 'lines' in m)
    out = []
    for entry in report['lines']:
        if 'segs' in entry:
            out.append(''.join(seg['t'] for seg in entry['segs']))
        else:
            out.append((entry.get('k', '') or '') + (entry.get('v', '') or ''))
    return report['lines'], out


class ListingTests(TransactionTestCase):
    """#123: vendor list columns and Slot cells."""

    async def test_vendor_list_columns_and_cells(self):
        zone, room = await sync_to_async(make_world)('la')

        def setup():
            char = make_character('la', room)
            sword = make_def('la', 'Iron Sword', 'weapon',
                             valid_slots=['MAIN_HAND'], takes_durability=True)
            hide = make_def('la', 'Animal Hide')
            make_vendor('la', room, [(sword, 12), (hide, 3)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_list()
        lines, texts = line_texts(sent)

        header = next(t for t in texts if 'Slot' in t and 'Name' in t)
        self.assertNotIn('Quantity', header)
        self.assertIn('Details', header)
        self.assertIn('Price', header)

        sword_row = next(t for t in texts if 'Iron Sword' in t)
        self.assertIn('Main hand', sword_row)
        # Details is rarity only — no durability, no binding flag.
        self.assertNotIn('100%', sword_row)
        self.assertNotIn('Bound', sword_row)
        self.assertIn('Common', sword_row)

        hide_row = next(t for t in texts if 'Animal Hide' in t)
        self.assertTrue(hide_row.strip().startswith('-'))

    async def test_inventory_slot_cell_populated(self):
        zone, room = await sync_to_async(make_world)('lb')

        def setup():
            char = make_character('lb', room)
            helm = make_def('lb', 'Iron Helm', 'armor', valid_slots=['HEAD'])
            ItemInstance.objects.create(
                definition=helm, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_inventory()
        lines, texts = line_texts(sent)
        helm_row = next(t for t in texts if 'Iron Helm' in t
                        and 'Head' in t.split('Iron Helm')[0])
        self.assertTrue(helm_row.strip().startswith('Head'))


class VersionLineTests(TransactionTestCase):
    """#120: the version constant closes help."""

    async def test_help_ends_with_the_version_line(self):
        zone, room = await sync_to_async(make_world)('vh')
        char = await sync_to_async(make_character)('vh', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_help()
        lines, texts = line_texts(sent)
        self.assertEqual(lines[-1], {'k': 'Version:', 'v': f' {SHYLAND_VERSION}'})
        self.assertEqual(lines[-2], {})
        self.assertEqual(SHYLAND_VERSION, '22.0-DEV')


class CategoryRetagTests(TransactionTestCase):
    """#124: Combat has ended + loot lines carry the success/loot class."""

    async def test_loot_line_is_loot_colored(self):
        zone, room = await sync_to_async(make_world)('cr')

        def setup():
            char = make_character('cr', room)
            definition = NpcDefinition.objects.create(
                name='cr boar', slug='cr-boar',
                description='x', genre_tag='fantasy',
                base_vitality=10, base_str=1, base_dex=1, base_end=1,
                base_int=1, base_wis=1, base_per=1,
            )
            corpse = Corpse.objects.create(
                npc_definition=definition, npc_name_snapshot='the cr boar',
                current_room=room, killed_by=char, copper_drop=0,
                decay_at=timezone.now() + timedelta(hours=1),
            )
            hide = make_def('cr', 'Animal Hide')
            ItemInstance.objects.create(
                definition=hide, corpse=corpse, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_loot('boar')
        loot_lines = [m for m in outputs(sent)
                      if m['text'].startswith('You loot Animal Hide')]
        self.assertEqual(len(loot_lines), 1)
        self.assertEqual(loot_lines[0]['category'], 'reward')

    async def test_combat_has_ended_is_success_colored(self):
        def setup():
            zone, room = make_world('ce')
            char = make_character('ce', room)
            Character.objects.filter(pk=char.pk).update(
                vitality_current=500, vitality_max=500, stat_str=100)
            definition = NpcDefinition.objects.create(
                name='ce beetle', slug='ce-beetle',
                description='x', genre_tag='fantasy',
                base_vitality=1, base_str=1, base_dex=1, base_end=1,
                base_int=1, base_wis=1, base_per=1,
            )
            npc = NpcInstance.objects.create(
                definition=definition, current_room=room, spawn_room=room,
                vitality_current=1, vitality_max=1,
            )
            from apps.shyland.models import COMBAT_ROUND_TICKS
            session = CombatSession.objects.create(
                room=room, last_tick_at=timezone.now(),
                tick_counter=COMBAT_ROUND_TICKS - 1,
            )
            session.characters.add(char)
            session.npcs.add(npc)
            return char
        char = await sync_to_async(setup)()

        from apps.shyland.management.commands.run_tick_engine import Command
        cmd = Command()
        player_msgs = []

        async def record_send(character_pk, text, category, status,
                              event=None, fight=None):
            if text:
                player_msgs.append((text, category))

        async def record_broadcast(room_id, text, category='room',
                                   exclude_pk=None, exclude_pks=None):
            pass
        cmd.send_to_player = record_send
        cmd.broadcast_to_room = record_broadcast

        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='hit'):
            await cmd.process_combat(1)

        ended = [m for m in player_msgs if m[0] == 'Combat has ended.']
        self.assertEqual(len(ended), 1)
        self.assertEqual(ended[1 - 1][1], 'reward')


class VocabularyTests(SimpleTestCase):
    """Step 1: Bound/Unbound only — no Droppable/Undroppable anywhere in
    player-facing output, help, or completion strings."""

    def test_no_dead_vocabulary_in_sources(self):
        import inspect
        from apps.shyland import consumers, item_utils, command_grammar
        from pathlib import Path
        for module in (consumers, item_utils, command_grammar):
            source = inspect.getsource(module)
            self.assertNotIn('Droppable', source, module.__name__)
            self.assertNotIn('Undroppable', source, module.__name__)
        template = Path(consumers.__file__).parent / 'templates' / 'shyland' / 'game.html'
        html = template.read_text()
        self.assertNotIn('Droppable', html)
        self.assertNotIn('Undroppable', html)

    def test_help_sections_carry_no_dead_vocabulary(self):
        # Rows may carry a fourth admin-flag element since v22 brief 3.
        for _, rows in SkylandConsumer.HELP_SECTIONS:
            for row in rows:
                for text in row[:3]:
                    self.assertNotIn('Droppable', text)
                    self.assertNotIn('Undroppable', text)
