"""v23 brief 2 (#137, #18): item data integrity.

Corpse contents CASCADE with the corpse (no orphans from any
corpse-deletion path), the exactly-one location invariant on
ItemInstance.save() (zero and multiple locations both rejected), the
self-verifying one-time purge_orphaned_items command, and inventory
stacking for all wear-free item types keyed on (definition, mk_tier,
rarity, soulbound state)."""

from datetime import timedelta
from io import StringIO

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.models import Corpse, ItemInstance
from apps.shyland.tests.test_b2_amendment1 import line_texts
from apps.shyland.tests.test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world,
)


def make_corpse(room):
    return Corpse.objects.create(
        npc_name_snapshot='the test snarler',
        current_room=room,
        decay_at=timezone.now() + timedelta(minutes=30),
    )


def corpse_item(defn, corpse):
    return ItemInstance.objects.create(
        definition=defn, corpse=corpse, mk_tier=1, rarity='common',
        durability_current=100.0, is_identified=True,
    )


class CorpseCascadeTests(TestCase):
    """#137 part 2: ItemInstance.corpse is on_delete=CASCADE — contents
    die with the corpse on any ORM delete path."""

    def test_corpse_delete_cascades_contents(self):
        zone, room = make_world('diA')
        defn = make_item_def('diA', 'Animal Hide')
        corpse = make_corpse(room)
        items = [corpse_item(defn, corpse) for _ in range(3)]
        bystander = ItemInstance.objects.create(
            definition=defn, current_room=room, mk_tier=1, rarity='common',
        )

        # The same queryset-delete shape the tick engine's delete_corpse
        # uses — the collector must cascade the contents.
        Corpse.objects.filter(pk=corpse.pk).delete()

        self.assertFalse(
            ItemInstance.objects.filter(pk__in=[i.pk for i in items]).exists())
        self.assertTrue(ItemInstance.objects.filter(pk=bystander.pk).exists())


class LocationInvariantTests(TestCase):
    """#137 part 3: save() demands exactly one of owner / current_room /
    corpse — zero locations no longer passes silently."""

    def setUp(self):
        self.zone, self.room = make_world('diB')
        self.char = make_character('diB', self.room)
        self.defn = make_item_def('diB', 'Animal Hide')
        self.corpse = make_corpse(self.room)

    def test_zero_locations_raises(self):
        with self.assertRaises(ValidationError):
            ItemInstance(
                definition=self.defn, mk_tier=1, rarity='common',
            ).save()

    def test_two_locations_raises(self):
        with self.assertRaises(ValidationError):
            ItemInstance(
                definition=self.defn, owner=self.char,
                current_room=self.room, mk_tier=1, rarity='common',
            ).save()

    def test_owner_only_saves(self):
        ItemInstance(
            definition=self.defn, owner=self.char,
            mk_tier=1, rarity='common',
        ).save()

    def test_room_only_saves(self):
        ItemInstance(
            definition=self.defn, current_room=self.room,
            mk_tier=1, rarity='common',
        ).save()

    def test_corpse_only_saves(self):
        ItemInstance(
            definition=self.defn, corpse=self.corpse,
            mk_tier=1, rarity='common',
        ).save()


class PurgeOrphanedItemsTests(TestCase):
    """#137 part 4: the one-time purge — exact filter, run-time counts,
    post-run zero-count self-verification, idempotent."""

    def _make_orphans(self, defn, room, count):
        # Production orphans were created by the pre-CASCADE decay sweep's
        # SET_NULL, never by save(). Mirror that: create in a corpse, then
        # orphan via a queryset .update() that bypasses save().
        corpse = make_corpse(room)
        items = [corpse_item(defn, corpse) for _ in range(count)]
        pks = [i.pk for i in items]
        ItemInstance.objects.filter(pk__in=pks).update(corpse=None)
        Corpse.objects.filter(pk=corpse.pk).delete()
        return pks

    def test_purge_deletes_orphans_only_and_verifies(self):
        zone, room = make_world('diC')
        char = make_character('diC', room)
        defn = make_item_def('diC', 'Animal Hide')
        orphan_pks = self._make_orphans(defn, room, 3)

        keeper_corpse = make_corpse(room)
        keepers = [
            ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=1, rarity='common'),
            ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1, rarity='common'),
            ItemInstance.objects.create(
                definition=defn, corpse=keeper_corpse, mk_tier=1, rarity='common'),
        ]

        out = StringIO()
        call_command('purge_orphaned_items', stdout=out)
        text = out.getvalue()

        self.assertIn('3 orphaned item instance(s) found.', text)
        self.assertIn('3 deleted; 0 remaining.', text)
        self.assertIn('database clean', text)
        self.assertFalse(
            ItemInstance.objects.filter(pk__in=orphan_pks).exists())
        for keeper in keepers:
            self.assertTrue(ItemInstance.objects.filter(pk=keeper.pk).exists())

    def test_second_run_is_a_clean_noop(self):
        zone, room = make_world('diD')
        defn = make_item_def('diD', 'Animal Hide')
        self._make_orphans(defn, room, 2)

        call_command('purge_orphaned_items', stdout=StringIO())
        out = StringIO()
        call_command('purge_orphaned_items', stdout=out)
        text = out.getvalue()

        self.assertIn('0 orphaned item instance(s) found.', text)
        self.assertIn('0 deleted; 0 remaining.', text)
        self.assertIn('database clean', text)


class InventoryStackingTests(TransactionTestCase):
    """#18: wear-free types (consumable/material/readable/key) stack in
    the inventory display on (definition, mk_tier, rarity, soulbound
    state); per-instance-identity types never stack."""

    def _rows_for(self, sent, name):
        lines, texts = line_texts(sent)
        return [t for t in texts if name in t]

    async def _inventory_rows(self, prefix, item_type, name, unbound=0,
                              bound=0):
        zone, room = await sync_to_async(make_world)(prefix)

        def setup():
            char = make_character(prefix, room)
            defn = make_item_def(prefix, name, item_type)
            for _ in range(unbound):
                make_owned_item(defn, char)
            for _ in range(bound):
                make_owned_item(defn, char, bound=True)
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_inventory()
        return self._rows_for(sent, name)

    async def test_materials_stack_into_one_row(self):
        rows = await self._inventory_rows(
            'stA', 'material', 'Test Ore', unbound=3)
        self.assertEqual(len(rows), 1)
        self.assertIn('3', rows[0].split())

    async def test_bound_copy_never_merges_with_unbound(self):
        rows = await self._inventory_rows(
            'stB', 'material', 'Test Ore', unbound=2, bound=1)
        self.assertEqual(len(rows), 2)
        bound_rows = [r for r in rows if 'Bound' in r.split()]
        unbound_rows = [r for r in rows if 'Unbound' in r.split()]
        self.assertEqual(len(bound_rows), 1)
        self.assertEqual(len(unbound_rows), 1)
        self.assertIn('1', bound_rows[0].split())
        self.assertIn('2', unbound_rows[0].split())

    async def test_consumables_still_stack(self):
        rows = await self._inventory_rows(
            'stC', 'consumable', 'Test Tonic', unbound=3)
        self.assertEqual(len(rows), 1)
        self.assertIn('3', rows[0].split())

    async def test_consumable_bound_unbound_split(self):
        # The ruled key deliberately tightens consumable stacking too: a
        # bound stack and an unbound stack render as two rows.
        rows = await self._inventory_rows(
            'stD', 'consumable', 'Test Tonic', unbound=2, bound=2)
        self.assertEqual(len(rows), 2)

    async def test_weapons_never_stack(self):
        rows = await self._inventory_rows(
            'stE', 'weapon', 'Test Blade', unbound=3)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertIn('1', row.split())

    async def test_readables_stack(self):
        rows = await self._inventory_rows(
            'stF', 'readable', 'Test Scroll', unbound=2)
        self.assertEqual(len(rows), 1)
        self.assertIn('2', rows[0].split())

    async def test_keys_stack(self):
        rows = await self._inventory_rows(
            'stG', 'key', 'Test Key', unbound=2)
        self.assertEqual(len(rows), 1)
        self.assertIn('2', rows[0].split())
