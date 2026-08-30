"""v24.11 Brief 1 — knowledge by holding (#80).

Pickup identifies, drop re-veils, `examine` is close inspection that
reveals real details without pickup — output-only, never persisted.
Both flips live only at the ownership-transfer choke points and carry
the is_unidentifiable guard. The unidentified item line is mystery name
+ [Bound|Unbound] with no info suffix of any kind, and resolution/tab
completion match visible names only — the real name never leaks through
the grammar.
"""

from asgiref.sync import sync_to_async
from datetime import timedelta

from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.command_grammar import complete, resolve
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.item_utils import (
    compose_item_line, get_display_name, get_item_suffix,
)
from apps.shyland.models import (
    Corpse, ItemDefinition, ItemInstance, NpcDefinition,
)

from .test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)

BASE_TIME = timezone.now() - timedelta(days=1)


def make_veiled_def(prefix, name, item_type='weapon', mystery='',
                    takes_durability=False, carry_pct_base=0):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type=item_type, genre_tag='fantasy',
        valid_slots=['MAIN_HAND'] if item_type == 'weapon' else [],
        scaling_base=0.0, scaling_factor=0.0, base_value=1,
        takes_durability_loss=takes_durability,
        mystery_name=mystery, carry_pct_base=carry_pct_base,
        # v25.12 (#311): wearing fixtures get an explicit all-worn band —
        # preserves the retired empty-table fallback they ran under.
        durability_table=([{'min': 0, 'max': 100, 'penalty': 1.0}]
                          if takes_durability else []),
    )


def mem_def(pk, name, item_type='weapon', mystery='',
            takes_durability=False, carry_pct_base=0):
    return ItemDefinition(
        pk=pk, name=name, slug=f'memdef-{pk}', item_type=item_type,
        genre_tag='fantasy', valid_slots=[],
        scaling_base=0.0, scaling_factor=0.0,
        takes_durability_loss=takes_durability,
        mystery_name=mystery, carry_pct_base=carry_pct_base,
    )


def mem_item(pk, defn, identified=True, dur=100.0, unidentifiable=False):
    item = ItemInstance(
        pk=pk, mk_tier=1, rarity='common', durability_current=dur,
        is_equipped=False, is_soulbound=False,
        is_identified=identified, is_unidentifiable=unidentifiable,
    )
    item.definition = defn
    item.created_at = BASE_TIME + timedelta(seconds=pk)
    return item


class TransferFlipTests(TransactionTestCase):
    """Cases 1-4: the ownership-transfer flips and their guards."""

    async def test_1_pickup_identifies_persisted(self):
        def setup():
            zone, room = make_world('kh1')
            char = make_character('kh1', room)
            defn = make_veiled_def('kh1', 'Gleamsteel Saber',
                                   mystery='a strange lump')
            item = ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=False,
            )
            return char, item
        char, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('pickup', 'lump')

        def check():
            item.refresh_from_db()
            return item.is_identified, item.owner_id
        identified, owner_id = await sync_to_async(check)()
        self.assertTrue(identified)
        self.assertEqual(owner_id, char.pk)

    async def test_2_pickup_unidentifiable_guard(self):
        def setup():
            zone, room = make_world('kh2')
            char = make_character('kh2', room)
            defn = make_veiled_def('kh2', 'Nameless Shard',
                                   item_type='material',
                                   mystery='a strange shard')
            item = ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=False, is_unidentifiable=True,
            )
            return char, item
        char, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('pickup', 'shard')

        def check():
            item.refresh_from_db()
            return item.is_identified, item.owner_id
        identified, owner_id = await sync_to_async(check)()
        self.assertFalse(identified)
        self.assertEqual(owner_id, char.pk)

    async def test_3_loot_flips_and_names_the_real_item(self):
        def setup():
            zone, room = make_world('kh3')
            char = make_character('kh3', room)
            npc_def = NpcDefinition.objects.create(
                name='kh3 boar', slug='kh3-boar', description='x',
                genre_tag='fantasy', base_vitality=10, base_str=1,
                base_dex=1, base_end=1, base_int=1, base_wis=1, base_per=1,
            )
            corpse = Corpse.objects.create(
                npc_definition=npc_def, npc_name_snapshot='the kh3 boar',
                current_room=room, killed_by=char,
                decay_at=timezone.now() + timedelta(hours=1),
            )
            defn = make_veiled_def('kh3', 'Gleamsteel Saber',
                                   mystery='a strange lump')
            item = ItemInstance.objects.create(
                definition=defn, corpse=corpse, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=False,
            )
            return char, item
        char, item = await sync_to_async(setup)()
        consumer = make_stub_consumer(char, [])
        name = await consumer.do_loot_item(item, char)
        self.assertEqual(name, 'Gleamsteel Saber')

        def check():
            item.refresh_from_db()
            return item.is_identified
        self.assertTrue(await sync_to_async(check)())

    async def test_3b_loot_unidentifiable_guard(self):
        def setup():
            zone, room = make_world('kh3b')
            char = make_character('kh3b', room)
            npc_def = NpcDefinition.objects.create(
                name='kh3b boar', slug='kh3b-boar', description='x',
                genre_tag='fantasy', base_vitality=10, base_str=1,
                base_dex=1, base_end=1, base_int=1, base_wis=1, base_per=1,
            )
            corpse = Corpse.objects.create(
                npc_definition=npc_def, npc_name_snapshot='the kh3b boar',
                current_room=room, killed_by=char,
                decay_at=timezone.now() + timedelta(hours=1),
            )
            defn = make_veiled_def('kh3b', 'Nameless Shard',
                                   item_type='material',
                                   mystery='a strange shard')
            item = ItemInstance.objects.create(
                definition=defn, corpse=corpse, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=False, is_unidentifiable=True,
            )
            return char, item
        char, item = await sync_to_async(setup)()
        consumer = make_stub_consumer(char, [])
        name = await consumer.do_loot_item(item, char)
        self.assertEqual(name, 'a strange shard')

        def check():
            item.refresh_from_db()
            return item.is_identified
        self.assertFalse(await sync_to_async(check)())

    async def test_4_drop_reveils_and_unidentifiable_guard_holds(self):
        def setup():
            zone, room = make_world('kh4')
            char = make_character('kh4', room)
            defn = make_veiled_def('kh4', 'Gleamsteel Saber',
                                   mystery='a strange lump')
            item = ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
            return char, room, item
        char, room, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('drop', 'saber')

        def check():
            item.refresh_from_db()
            return item.is_identified, item.current_room_id
        identified, room_id = await sync_to_async(check)()
        self.assertFalse(identified)
        self.assertEqual(room_id, room.pk)

        # The guard: an unidentifiable item's is_identified is never
        # written by the drop path either.
        def setup_unid():
            defn = make_veiled_def('kh4b', 'Nameless Shard',
                                   item_type='material',
                                   mystery='a strange shard')
            return ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0,
                is_identified=True, is_unidentifiable=True,
            )
        unid = await sync_to_async(setup_unid)()
        await consumer.transfer_to_room(unid, room)

        def check_unid():
            unid.refresh_from_db()
            return unid.is_identified
        self.assertTrue(await sync_to_async(check_unid)())


class VeilDisplayTests(SimpleTestCase):
    """Cases 5-6: no info suffix of any kind through the veil."""

    def test_5_suffix_empty_for_unidentified(self):
        worn_def = mem_def(1, 'Gleamsteel Saber', takes_durability=True)
        bag_def = mem_def(2, 'Duskhide Satchel', item_type='bag',
                          carry_pct_base=5)
        worn_unid = mem_item(11, worn_def, identified=False, dur=60.0)
        bag_unid = mem_item(12, bag_def, identified=False)
        self.assertEqual(get_item_suffix(worn_unid), '')
        self.assertEqual(get_item_suffix(bag_unid), '')
        # Unchanged output for the identified equivalents.
        worn_id = mem_item(13, worn_def, identified=True, dur=60.0)
        bag_id = mem_item(14, bag_def, identified=True)
        self.assertEqual(get_item_suffix(worn_id), '— 60% durability')
        # v24.23 (#215): the identified bag suffix is the percentage form
        # (Mk 1 instance, carry_pct_base 5, per-Mk 0 → 5%).
        self.assertEqual(get_item_suffix(bag_id), '— +5% carry capacity')

    def test_6_details_cell_gates_durability(self):
        worn_def = mem_def(3, 'Gleamsteel Saber', takes_durability=True)
        unid = mem_item(15, worn_def, identified=False, dur=60.0)
        segs = SkylandConsumer._details_cell(unid)
        self.assertEqual(segs, [('Unbound', 'flag-chrome')])
        # 60% sits in the 50-75 penalty band — the durability voice is
        # 'say' (band-derived, never this test's own threshold).
        ident = mem_item(16, worn_def, identified=True, dur=60.0)
        segs = SkylandConsumer._details_cell(ident)
        self.assertIn(('60%', 'say'), segs)
        self.assertEqual(segs[-1], ('Unbound', 'flag-chrome'))


class ExamineTests(TransactionTestCase):
    """Cases 7-8: examine is close inspection — output-only reveal."""

    async def test_7_examine_reveals_without_persisting(self):
        def setup():
            zone, room = make_world('kh7')
            char = make_character('kh7', room)
            defn = make_veiled_def('kh7', 'Gleamsteel Saber',
                                   mystery='a strange lump',
                                   takes_durability=True)
            item = ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=2,
                rarity='common', durability_current=60.0,
                is_identified=False,
                damage_midpoint=10.0, damage_spread=2.0,
            )
            return char, item
        char, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('examine', 'lump')

        [msg] = outputs(sent)
        self.assertEqual(msg['category'], 'report')
        # The full identified detail block: real name-with-tier and stats.
        self.assertIn('Gleamsteel Saber Mk 2', msg['text'])
        self.assertIn('Type:       Weapon', msg['text'])
        self.assertIn('Damage:     8 – 12', msg['text'])
        self.assertIn('Durability: 60%', msg['text'])
        self.assertNotIn('strange lump', msg['text'])

        # The reveal is output-only: nothing persisted, the room listing
        # composition still shows the mystery name.
        def check():
            item.refresh_from_db()
            return item.is_identified, get_display_name(item)
        identified, listed_name = await sync_to_async(check)()
        self.assertFalse(identified)
        self.assertEqual(listed_name, 'a strange lump')

    async def test_8_examine_unidentifiable_mystery_block(self):
        def setup():
            zone, room = make_world('kh8')
            char = make_character('kh8', room)
            # mystery_description deliberately blank: the display
            # description falls back to the one cannot-determine sentence.
            defn = make_veiled_def('kh8', 'Nameless Shard',
                                   item_type='material',
                                   mystery='a strange shard')
            item = ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1,
                rarity='rare', durability_current=100.0,
                is_identified=False, is_unidentifiable=True,
            )
            return char, item
        char, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('examine', 'shard')

        [msg] = outputs(sent)
        self.assertEqual(msg['text'], '\n'.join([
            'a strange shard  [Unbound]',
            '',
            "  You can't determine anything about this item.",
            '  No known method of identification will reveal its true nature.',
        ]))
        # Exactly one cannot-determine sentence (the redundant
        # parenthetical is gone), and never the real name.
        self.assertEqual(msg['text'].count('determine'), 1)
        self.assertNotIn('Nameless Shard', msg['text'])

        def check():
            item.refresh_from_db()
            return item.is_identified
        self.assertFalse(await sync_to_async(check)())


class GrammarVeilTests(SimpleTestCase):
    """Case 9: the real name never leaks through the grammar."""

    def test_9_reveiled_item_resolves_by_mystery_name_only(self):
        defn = mem_def(4, 'Gleamsteel Saber', mystery='a strange lump')
        item = mem_item(17, defn, identified=False)
        res = resolve('pickup', 'lump', [item])
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [item])
        res = resolve('pickup', 'saber', [item])
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'not_found')
        # Tab completion completes the mystery tokens, never the real ones.
        self.assertIn('lump', complete('pickup', 'lu', [item]))
        self.assertEqual(complete('pickup', 'sa', [item]), [])


class RoundTripTests(TransactionTestCase):
    """Case 10: identified → drop → veiled ground line → pickup → restored."""

    async def test_10_drop_pickup_round_trip(self):
        def setup():
            zone, room = make_world('kh10')
            char = make_character('kh10', room)
            # Blank mystery_name: the ground line uses the fallback
            # mystery form, per the playtest checklist's example.
            defn = make_veiled_def('kh10', 'Gleamsteel Saber',
                                   takes_durability=True)
            item = ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=2, rarity='common',
                durability_current=60.0, is_identified=True,
            )
            return char, item
        char, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('drop', 'saber')

        def ground_line():
            item.refresh_from_db()
            return compose_item_line(item)
        # Mystery name + [Unbound] only — no durability, no rarity, no Mk.
        self.assertEqual(await sync_to_async(ground_line)(),
                         'an unidentified weapon  [Unbound]')

        await consumer._dispatch('pickup', 'weapon')

        def carried_line():
            item.refresh_from_db()
            return item.is_identified, compose_item_line(item)
        identified, line = await sync_to_async(carried_line)()
        self.assertTrue(identified)
        self.assertEqual(
            line, 'Gleamsteel Saber Mk 2  — 60% durability  [Common, Unbound]')
