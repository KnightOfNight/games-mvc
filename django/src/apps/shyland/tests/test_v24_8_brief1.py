"""V24.8 Brief 1 (#197): dual-slot Slot cell.

The listing-table Slot cell stops hiding either-hand flexibility: an
item valid in more than one equip slot names all its slots — sentence-
case labels joined with '/' in authored valid_slots order ('Main
hand/Off hand'), the two-handed word appended once after the full
joined label. Single-slot and slotless cells are byte-identical to
v24.7. Scope is the shared _slot_cell helper only — inv's inventory
table and vendor list inherit together; the paper-doll, examine, and
all equip/combat mechanics are untouched.
"""

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import ItemDefinition, ItemInstance
from apps.shyland.tests.test_b2_amendment1 import line_texts, make_def
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, make_vendor, make_world,
)


def make_combat_knife(prefix):
    """Mirror of the seed Combat Knife's display-relevant fields —
    the only current dual-slot case (valid_slots authored order
    MAIN_HAND, OFF_HAND; one-handed)."""
    return ItemDefinition.objects.create(
        name='Combat Knife', slug=f'{prefix}-combat-knife',
        item_type='weapon', genre_tag='wasteland',
        valid_slots=['MAIN_HAND', 'OFF_HAND'],
        scaling_base=5.0, scaling_factor=2.0, base_value=10,
        takes_durability_loss=True,
        # v25.12 (#311): explicit all-worn band — preserves the
        # retired empty-table fallback these fixtures ran under.
        durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
    )


class DualSlotInventoryTests(TransactionTestCase):
    """#197: inv's inventory table names all valid slots."""

    async def test_combat_knife_inv_slot_cell(self):
        zone, room = await sync_to_async(make_world)('v8a')

        def setup():
            char = make_character('v8a', room)
            knife = make_combat_knife('v8a')
            ItemInstance.objects.create(
                definition=knife, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_inventory()
        lines, texts = line_texts(sent)
        knife_row = next(t for t in texts if 'Combat Knife' in t)
        self.assertTrue(
            knife_row.strip().startswith('Main hand/Off hand'))


class DualSlotVendorListTests(TransactionTestCase):
    """#197: vendor list inherits the joined label."""

    async def test_combat_knife_vendor_slot_cell(self):
        zone, room = await sync_to_async(make_world)('v8b')

        def setup():
            char = make_character('v8b', room)
            knife = make_combat_knife('v8b')
            make_vendor('v8b', room, [(knife, 12)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_list()
        lines, texts = line_texts(sent)
        knife_row = next(t for t in texts if 'Combat Knife' in t)
        self.assertTrue(
            knife_row.strip().startswith('Main hand/Off hand'))


class SlotCellCompositionTests(TransactionTestCase):
    """#197: the ruled composition, direct on the shared helper."""

    async def test_slot_cell_variants(self):
        def setup():
            knife = make_combat_knife('v8c')
            mace = make_def('v8c', 'Iron Mace', 'weapon',
                            valid_slots=['MAIN_HAND'],
                            takes_durability=True)
            bow = ItemDefinition.objects.create(
                name='Hunting Bow', slug='v8c-hunting-bow',
                item_type='weapon', genre_tag='fantasy',
                valid_slots=['RANGED'], scaling_base=3.0,
                scaling_factor=1.0, base_value=10,
                takes_durability_loss=True, is_two_handed=True,
                is_ranged=True,
                durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
            )
            hide = make_def('v8c', 'Animal Hide')
            # Synthetic dual-slot two-hander (#197 defensive ruling) —
            # no such item exists in seed; constructed in-test only.
            dual_two = ItemDefinition.objects.create(
                name='Test Greatblade', slug='v8c-test-greatblade',
                item_type='weapon', genre_tag='fantasy',
                valid_slots=['MAIN_HAND', 'OFF_HAND'], scaling_base=3.0,
                scaling_factor=1.0, base_value=10,
                takes_durability_loss=True, is_two_handed=True,
                durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
            )
            return knife, mace, bow, hide, dual_two
        knife, mace, bow, hide, dual_two = await sync_to_async(setup)()

        cell = SkylandConsumer._slot_cell
        # Dual-slot: all slots, '/'-joined, authored order.
        self.assertEqual(cell(knife), 'Main hand/Off hand')
        # Single-slot and slotless: byte-identical to v24.7.
        self.assertEqual(cell(mace), 'Main hand')
        self.assertEqual(cell(bow), 'Ranged (two-handed)')
        self.assertEqual(cell(hide), [('-', 'muted')])
        # Dual-slot two-hander: the word once, after the full label.
        self.assertEqual(cell(dual_two), 'Main hand/Off hand (two-handed)')

    async def test_authored_order_is_preserved(self):
        def setup():
            return ItemDefinition.objects.create(
                name='Test Parry Dagger', slug='v8d-test-parry-dagger',
                item_type='weapon', genre_tag='fantasy',
                valid_slots=['OFF_HAND', 'MAIN_HAND'], scaling_base=3.0,
                scaling_factor=1.0, base_value=10,
                takes_durability_loss=True,
                durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
            )
        reversed_def = await sync_to_async(setup)()
        self.assertEqual(SkylandConsumer._slot_cell(reversed_def),
                         'Off hand/Main hand')
