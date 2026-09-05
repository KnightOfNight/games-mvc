"""v25.15 brief 1 (#321): bulk buy/sell batching.

A bulk sale is one atomic transaction — one character lock, one copper
update, one bulk delete — replacing the per-item do_sell loop; buy
persists its instances in one bulk_create. Zero player-facing change:
these tests pin the money arithmetic, the row outcomes, the pk-keyed
group totals (the regression guard for the old pk-collapse defect), and
the query-count independence that is the structural proof of batching.
"""
from asgiref.sync import sync_to_async

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext

from apps.shyland import npc_voice
from apps.shyland.combat_utils import npc_display
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.currency import display_for_zone
from apps.shyland.item_utils import get_sale_price
from apps.shyland.models import Character, ItemInstance, VendorEntry

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_vendor, make_world, outputs,
)

# The undecorated engine methods, callable synchronously in tests (the
# established pattern — see test_combat_state / test_map_payload).
_do_buy = SkylandConsumer.__dict__['do_buy'].func
_do_sell_bulk = SkylandConsumer.__dict__['do_sell_bulk'].func


def make_rarity_item(defn, char, rarity):
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity=rarity,
        durability_current=100.0, is_identified=True,
    )


def carried_with_definitions(char):
    """The sell path's item shape: definitions preloaded (premise 7)."""
    return list(
        ItemInstance.objects.filter(owner=char).select_related('definition')
    )


class BulkSellTests(TransactionTestCase):
    """§4.4/§4.5 — one transaction, exact copper, exact rows."""

    async def test_bulk_sell_mixed_inventory(self):
        def setup():
            zone, room = make_world('bsA')
            char = make_character('bsA', room)
            mace_def = make_item_def('bsA', 'Iron Mace', item_type='weapon',
                                     base_value=9)
            hide_def = make_item_def('bsA', 'Animal Hide', base_value=30)
            mug_def = make_item_def('bsA', 'Cracked Mug', base_value=0)
            make_vendor('bsA', room, [(hide_def, 9)])
            sellable = ([make_owned_item(mace_def, char) for _ in range(3)]
                        + [make_owned_item(hide_def, char) for _ in range(2)]
                        + [make_owned_item(mug_def, char)])
            artifact = make_rarity_item(mace_def, char, 'artifact')
            expected_credit = sum(get_sale_price(i) for i in sellable)
            return char, sellable, artifact, char.copper, expected_credit
        (char, sellable, artifact,
         copper_before, expected_credit) = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all common')

        def state():
            return (
                ItemInstance.objects.filter(
                    pk__in=[i.pk for i in sellable]).count(),
                ItemInstance.objects.filter(pk=artifact.pk).exists(),
                Character.objects.get(pk=char.pk).copper,
            )
        sellable_left, artifact_exists, copper = await sync_to_async(state)()
        self.assertEqual(sellable_left, 0)
        self.assertTrue(artifact_exists)
        self.assertEqual(copper, copper_before + expected_credit)
        # The consumer's in-memory wallet synced with the batch.
        self.assertEqual(consumer.character.copper, copper)

    async def test_all_refused_batch_unchanged(self):
        # §4.5: an all-artifact batch never reaches do_sell_bulk — the
        # existing "nothing moved" refusal, wallet and rows untouched.
        def setup():
            zone, room = make_world('bsB')
            char = make_character('bsB', room)
            mace_def = make_item_def('bsB', 'Iron Mace', item_type='weapon',
                                     base_value=9)
            vendor = make_vendor('bsB', room, [(mace_def, 9)])
            artifact = make_rarity_item(mace_def, char, 'artifact')
            return char, vendor, artifact, char.copper
        char, vendor, artifact, copper_before = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all mace')

        texts = [m['text'] for m in outputs(sent)]
        expected = {npc_voice.pick(
            [line], vendor=npc_display(vendor, capitalize=True))
            for line in npc_voice.SELL_REFUSAL_NONE}
        self.assertTrue(any(t in expected for t in texts))

        def state():
            return (ItemInstance.objects.filter(pk=artifact.pk).exists(),
                    Character.objects.get(pk=char.pk).copper)
        artifact_exists, copper = await sync_to_async(state)()
        self.assertTrue(artifact_exists)
        self.assertEqual(copper, copper_before)

    async def test_group_total_integrity(self):
        # Spec 2: same definition + Mk at different prices (rarity varies
        # the multiplier) lands in one _aggregate_by_name group whose
        # total must be the true per-item sum — the regression guard for
        # the old pk-collapse defect, now guarding the pk-keyed shape.
        def setup():
            zone, room = make_world('bsC')
            char = make_character('bsC', room)
            mace_def = make_item_def('bsC', 'Iron Mace', item_type='weapon',
                                     base_value=9)
            vendor = make_vendor('bsC', room, [(mace_def, 9)])
            items = [make_owned_item(mace_def, char) for _ in range(2)]
            items.append(make_rarity_item(mace_def, char, 'uncommon'))
            total = sum(get_sale_price(i) for i in items)
            prices = sorted(get_sale_price(i) for i in items)
            amount = display_for_zone(total, zone.slug)
            return char, vendor, items, char.copper, total, prices, amount
        (char, vendor, items, copper_before,
         total, distinct_prices, amount) = await sync_to_async(setup)()
        # The fixture only guards the defect if prices really differ.
        self.assertGreater(distinct_prices[-1], distinct_prices[0])

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all mace')

        texts = [m['text'] for m in outputs(sent)]
        expected = {npc_voice.pick(
            [line], vendor=npc_display(vendor, capitalize=True),
            name='Iron Mace Mk 1', qty=3, amount=amount)
            for line in npc_voice.SELL_BULK}
        self.assertEqual(len([t for t in texts if t in expected]), 1)

        copper = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).copper)()
        self.assertEqual(copper, copper_before + total)

    def test_bulk_sell_query_count_independent(self):
        # Spec 3: the structural proof — do_sell_bulk's query count does
        # not grow with batch size (stronger than pinning a number).
        zone, room = make_world('bsD')
        char = make_character('bsD', room)
        hide_def = make_item_def('bsD', 'Animal Hide', base_value=30)
        consumer = make_stub_consumer(char, [])

        counts = []
        for size in (10, 50):
            for _ in range(size):
                make_owned_item(hide_def, char)
            items = carried_with_definitions(char)
            self.assertEqual(len(items), size)
            with CaptureQueriesContext(connection) as ctx:
                prices = _do_sell_bulk(consumer, items, char)
            counts.append(len(ctx.captured_queries))
            self.assertEqual(len(prices), size)
            self.assertEqual(ItemInstance.objects.filter(owner=char).count(), 0)
        self.assertEqual(counts[0], counts[1])


class BulkBuyTests(TransactionTestCase):
    """§4.3 — one bulk_create, contract and sentinels unchanged."""

    def _shop(self, prefix, price=9, copper=100_000):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        Character.objects.filter(pk=char.pk).update(copper=copper)
        char.refresh_from_db()
        defn = make_item_def(prefix, 'Healing Draught',
                             item_type='consumable', base_value=3)
        defn.primary_stats = [{'stat': 'str', 'base': 2.0, 'factor': 1.0}]
        defn.save(update_fields=['primary_stats'])
        make_vendor(prefix, room, [(defn, price)])
        entry = VendorEntry.objects.get(item_definition=defn)
        consumer = make_stub_consumer(char, [])
        return char, defn, entry, consumer

    def test_bulk_buy_correctness(self):
        char, defn, entry, consumer = self._shop('bbA')
        copper_before = char.copper

        items = _do_buy(consumer, entry, char, qty=40)

        self.assertEqual(len(items), 40)
        rows = ItemInstance.objects.filter(owner=char, definition=defn)
        self.assertEqual(rows.count(), 40)
        for item in items:
            self.assertIsNotNone(item.pk)
        for row in rows:
            self.assertTrue(row.rolled_primary_stats)
            self.assertFalse(row.is_soulbound)
        char.refresh_from_db()
        self.assertEqual(char.copper, copper_before - entry.price * 40)
        self.assertEqual(consumer.character.copper, char.copper)
        entry.refresh_from_db()
        self.assertEqual(entry.sold_count, 40)

    def test_bulk_buy_query_count_independent(self):
        # Spec 5: one bulk_create batch either way (batch_size 500).
        char, defn, entry, consumer = self._shop('bbB')
        counts = []
        for qty in (5, 40):
            with CaptureQueriesContext(connection) as ctx:
                items = _do_buy(consumer, entry, char, qty=qty)
            counts.append(len(ctx.captured_queries))
            self.assertEqual(len(items), qty)
        self.assertEqual(counts[0], counts[1])

    def test_buy_poor_sentinel(self):
        char, defn, entry, consumer = self._shop('bbC', price=9, copper=5)
        result = _do_buy(consumer, entry, char, qty=1)
        self.assertEqual(result, 'poor')
        self.assertEqual(ItemInstance.objects.filter(owner=char).count(), 0)
        char.refresh_from_db()
        self.assertEqual(char.copper, 5)

    def test_buy_sold_out_sentinel(self):
        char, defn, entry, consumer = self._shop('bbD')
        VendorEntry.objects.filter(pk=entry.pk).update(
            stock_limit=3, sold_count=2)
        entry.refresh_from_db()
        result = _do_buy(consumer, entry, char, qty=2)
        self.assertEqual(result, 'sold_out')
        self.assertEqual(ItemInstance.objects.filter(owner=char).count(), 0)
        entry.refresh_from_db()
        self.assertEqual(entry.sold_count, 2)


class LocationInvariantTests(TransactionTestCase):
    """§4.2 — the extracted helper and the save() path both enforce."""

    def test_helper_raises_on_zero_locations(self):
        item = ItemInstance()
        with self.assertRaises(ValidationError):
            item.enforce_location_invariant()

    def test_helper_raises_on_two_locations(self):
        item = ItemInstance(owner_id=1, corpse_id=1)
        with self.assertRaises(ValidationError):
            item.enforce_location_invariant()

    def test_helper_passes_on_exactly_one(self):
        ItemInstance(owner_id=1).enforce_location_invariant()
        ItemInstance(current_room_id=1).enforce_location_invariant()
        ItemInstance(corpse_id=1).enforce_location_invariant()

    def test_save_still_enforces(self):
        zone, room = make_world('liA')
        defn = make_item_def('liA', 'Animal Hide')
        item = ItemInstance(
            definition=defn, mk_tier=1, rarity='common',
            durability_current=100.0, is_identified=True,
        )
        with self.assertRaises(ValidationError):
            item.save()
