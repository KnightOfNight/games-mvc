"""V24.16 Brief 1 (#208): the inv trim.

`inv` / `inventory` renders the Inventory table alone — the paper-doll
belongs to bare `equip` (#195), the money line to `wallet`. The
equipped-items query stays alive: capacity still reads effective STR
(base + gear, #100) × 10, scaled by the equipped-bag percentage
(v24.23, #215). The help row says exactly what the command now does.
"""

from asgiref.sync import sync_to_async

from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland.consumers import SLOT_ORDER, SkylandConsumer
from apps.shyland.models import ItemDefinition, ItemInstance
from apps.shyland.tests.test_b2_amendment1 import line_texts
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, make_world,
)


def make_def(prefix, name, item_type, valid_slots=None, carry_pct_base=0):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type=item_type, genre_tag='fantasy',
        valid_slots=valid_slots or [],
        scaling_base=0.0, scaling_factor=0.0, base_value=1,
        carry_pct_base=carry_pct_base,
        # v25.12 (#311): explicit all-worn band — preserves the
        # retired empty-table fallback these fixtures ran under.
        durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
    )


def make_instance(defn, char, slot=None, primary=None):
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity='common',
        durability_current=100.0, is_identified=True,
        is_equipped=slot is not None, equipped_slot=slot or '',
        rolled_primary_stats=primary or [],
    )


class InvTrimTests(TransactionTestCase):
    """#208: the single-table render, with the capacity math alive."""

    async def _inv_output(self, prefix):
        """Char with a helm equipped (rolled +2 STR), a bag equipped
        (+5% carry, v24.23), and one slotless material carried; returns
        the report lines/texts of `inv`."""
        zone, room = await sync_to_async(make_world)(prefix)

        def setup():
            char = make_character(prefix, room)
            helm = make_def(prefix, 'Iron Helm', 'armor',
                            valid_slots=['HEAD'])
            bag = make_def(prefix, 'Duskhide Satchel', 'bag',
                           valid_slots=['BACK'], carry_pct_base=5)
            ore = make_def(prefix, 'Test Ore', 'material')
            make_instance(helm, char, slot='HEAD',
                          primary=[{'stat': 'str', 'value': 2}])
            make_instance(bag, char, slot='BACK')
            make_instance(ore, char)
            return char
        char = await sync_to_async(setup)()

        sent = []
        await make_stub_consumer(char, sent).cmd_inventory()
        return line_texts(sent)

    async def test_first_line_is_the_inventory_header(self):
        lines, texts = await self._inv_output('i16a')
        # No leading blank line — the header is the render's first line;
        # no Equipment header anywhere.
        self.assertTrue(texts[0].startswith('Inventory ('))
        self.assertTrue(texts[0].endswith('...'))
        self.assertFalse(any(t.startswith('Equipment') for t in texts))

    async def test_no_paper_doll_rows(self):
        lines, texts = await self._inv_output('i16b')
        # The equipped items' names never render; no slot-label rows
        # (the only carried item is slotless, so any row opening with a
        # slot label could only be a doll row).
        self.assertFalse(any('Iron Helm' in t for t in texts))
        self.assertFalse(any('Duskhide Satchel' in t for t in texts))
        slot_labels = [s.replace('_', ' ').capitalize() for s in SLOT_ORDER]
        for label in slot_labels:
            self.assertFalse(
                any(t.strip().startswith(label) for t in texts), label)

    async def test_no_wallet_line(self):
        lines, texts = await self._inv_output('i16c')
        self.assertFalse(any('Wallet' in t for t in texts))
        self.assertFalse(any(
            (entry.get('k') or '').startswith('Wallet')
            for entry in lines if 'segs' not in entry))

    async def test_capacity_reads_effective_str_plus_bag_bonus(self):
        lines, texts = await self._inv_output('i16d')
        # stat_str default 10 + rolled +2 on the equipped helm = 12
        # effective STR; ×10 = 120, scaled by the equipped bag's 5%
        # (v24.23, #215): 120 × 105 // 100 = 126. One unequipped item
        # carried. The equipped query is alive.
        self.assertEqual(texts[0], 'Inventory (1/126)...')


class HelpRowTests(SimpleTestCase):
    """#208: the help table describes the trimmed command."""

    def test_inventory_help_row(self):
        info_rows = dict(SkylandConsumer.HELP_SECTIONS)['Information commands']
        self.assertIn(
            ('inventory (inv)', 'inventory', 'Show your inventory.'),
            info_rows)
