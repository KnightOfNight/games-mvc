"""v23.1 brief 1 (#150, GDD §9.1 fn 19): the bulk-sell consumable guard.

Exactly the noun-less 'sell all <rarity>' form excludes consumables —
keyed on the absence of a noun token, never on what a noun matched.
Every noun-carrying form reaches consumables normally; bare 'sell all'
keeps the v22 teaching refusal; drop is untouched. Skips are announced
(one warn note after the sale lines); an all-consumables match is a
world-declined refusal, not a bare "nothing to sell."
"""
from asgiref.sync import sync_to_async

from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland.command_grammar import resolve
from apps.shyland.models import Character, ItemInstance

from .test_command_grammar import make_def, make_item
from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_vendor, make_world, outputs,
)

# The authored wording — verbatim per the brief, never paraphrased.
SKIP_NOTE = ("Your consumables stay in your pack — name them "
             "('sell all draught') to sell them.")
ALL_CONSUMABLES_REFUSAL = ("That's all consumables — name them "
                           "('sell all draught') if you mean to sell them.")
BARE_ALL_REFUSAL = ("Sell all of what? "
                    "Try 'sell all <item>' or 'sell all <rarity>'.")


class ResolverGuardTests(SimpleTestCase):
    """The guard at the resolver, on in-memory candidates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.draught_def = make_def(1, 'Healing Draught', 'consumable')
        cls.hide_def = make_def(2, 'Animal Hide', 'material')
        cls.blade_def = make_def(3, 'Rusty Blade', 'weapon',
                                 valid_slots=['MAIN_HAND'])
        cls.draughts = [make_item(101 + i, cls.draught_def) for i in range(3)]
        cls.hides = [make_item(111 + i, cls.hide_def) for i in range(2)]
        cls.blade = make_item(121, cls.blade_def)
        cls.carried = cls.draughts + cls.hides + [cls.blade]

    def test_nounless_bulk_excludes_consumables_and_flags(self):
        res = resolve('sell', 'all common', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(self.hides + [self.blade]))
        self.assertTrue(res.bulk_excluded)

    def test_no_consumables_in_pool_no_flag(self):
        res = resolve('sell', 'all common', self.hides + [self.blade])
        self.assertTrue(res.ok)
        self.assertFalse(res.bulk_excluded)

    def test_all_consumables_refused_world_declined(self):
        res = resolve('sell', 'all common', self.draughts)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'bulk_excluded')
        self.assertEqual(res.message, ALL_CONSUMABLES_REFUSAL)

    def test_noun_form_bypasses_guard(self):
        res = resolve('sell', 'all draught', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(self.draughts))
        self.assertFalse(res.bulk_excluded)

    def test_rarity_plus_noun_bypasses_guard(self):
        res = resolve('sell', 'all common draught', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(self.draughts))
        self.assertFalse(res.bulk_excluded)

    def test_numeric_form_bypasses_guard(self):
        res = resolve('sell', '2 draught', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(len(res.items), 2)
        for item in res.items:
            self.assertEqual(item.definition, self.draught_def)

    def test_single_form_bypasses_guard(self):
        res = resolve('sell', 'draught', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items[0].definition, self.draught_def)

    def test_bare_sell_all_teaching_refusal_unchanged(self):
        res = resolve('sell', 'all', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'bare_all')
        self.assertEqual(res.message, BARE_ALL_REFUSAL)

    def test_loot_bare_all_still_reaches_consumables(self):
        # The guard is sell policy only — other bulk verbs are untouched.
        res = resolve('loot', 'all', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(self.carried))
        self.assertFalse(res.bulk_excluded)


class ConsumerGuardTests(TransactionTestCase):
    """The guard end-to-end through cmd_sell: output, wallet, rows."""

    def _skip_notes(self, sent):
        return [(i, m.get('category')) for i, m in enumerate(outputs(sent))
                if m['text'] == SKIP_NOTE]

    async def test_mixed_bulk_sell_keeps_consumables_one_note(self):
        def setup():
            zone, room = make_world('bgA')
            char = make_character('bgA', room)
            draught_def = make_item_def('bgA', 'Healing Draught',
                                        item_type='consumable', base_value=3)
            hide_def = make_item_def('bgA', 'Animal Hide', base_value=3)
            blade_def = make_item_def('bgA', 'Rusty Blade',
                                      item_type='weapon', base_value=3)
            make_vendor('bgA', room, [(hide_def, 9)])
            draughts = [make_owned_item(draught_def, char) for _ in range(3)]
            hides = [make_owned_item(hide_def, char) for _ in range(2)]
            blade = make_owned_item(blade_def, char)
            equipped = ItemInstance.objects.create(
                definition=blade_def, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True, is_equipped=True,
            )
            return char, draughts, hides, blade, equipped, char.copper
        (char, draughts, hides, blade,
         equipped, copper_before) = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all common')

        notes = self._skip_notes(sent)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0][1], 'warn')
        # The note follows the sale lines — it is last in the sell output.
        self.assertEqual(notes[0][0], len(outputs(sent)) - 1)

        def state():
            return (
                ItemInstance.objects.filter(
                    pk__in=[d.pk for d in draughts]).count(),
                ItemInstance.objects.filter(
                    pk__in=[h.pk for h in hides]).count(),
                ItemInstance.objects.filter(pk=blade.pk).exists(),
                ItemInstance.objects.filter(pk=equipped.pk).exists(),
                Character.objects.get(pk=char.pk).copper,
            )
        (draughts_left, hides_left, blade_exists,
         equipped_exists, copper_after) = await sync_to_async(state)()
        self.assertEqual(draughts_left, 3)       # every consumable kept
        self.assertEqual(hides_left, 0)          # materials still sweep
        self.assertFalse(blade_exists)           # unequipped gear sold
        self.assertTrue(equipped_exists)         # equipped exclusion intact
        self.assertGreater(copper_after, copper_before)

    async def test_all_consumables_match_refuses_sells_nothing(self):
        def setup():
            zone, room = make_world('bgB')
            char = make_character('bgB', room)
            draught_def = make_item_def('bgB', 'Healing Draught',
                                        item_type='consumable', base_value=3)
            make_vendor('bgB', room, [(draught_def, 9)])
            draughts = [make_owned_item(draught_def, char) for _ in range(3)]
            return char, draughts, char.copper
        char, draughts, copper_before = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all common')

        lines = outputs(sent)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['text'], ALL_CONSUMABLES_REFUSAL)
        self.assertEqual(lines[0]['category'], 'warn')

        def state():
            return (ItemInstance.objects.filter(
                        pk__in=[d.pk for d in draughts]).count(),
                    Character.objects.get(pk=char.pk).copper)
        draughts_left, copper_after = await sync_to_async(state)()
        self.assertEqual(draughts_left, 3)
        self.assertEqual(copper_after, copper_before)

    async def test_named_forms_still_sell_consumables(self):
        def setup():
            zone, room = make_world('bgC')
            char = make_character('bgC', room)
            draught_def = make_item_def('bgC', 'Healing Draught',
                                        item_type='consumable', base_value=3)
            make_vendor('bgC', room, [(draught_def, 9)])
            return char, [make_owned_item(draught_def, char) for _ in range(6)]
        char, draughts = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('draught')          # single: oldest
        await consumer.cmd_sell('2 draught')        # numeric count
        await consumer.cmd_sell('all common draught')  # rarity + noun

        def remaining():
            return ItemInstance.objects.filter(
                pk__in=[d.pk for d in draughts]).count()
        self.assertEqual(await sync_to_async(remaining)(), 0)
        self.assertEqual(self._skip_notes(sent), [])

    async def test_sell_all_draught_sells_all(self):
        def setup():
            zone, room = make_world('bgD')
            char = make_character('bgD', room)
            draught_def = make_item_def('bgD', 'Healing Draught',
                                        item_type='consumable', base_value=3)
            make_vendor('bgD', room, [(draught_def, 9)])
            return char, [make_owned_item(draught_def, char) for _ in range(3)]
        char, draughts = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all draught')

        def remaining():
            return ItemInstance.objects.filter(
                pk__in=[d.pk for d in draughts]).count()
        self.assertEqual(await sync_to_async(remaining)(), 0)
        self.assertEqual(self._skip_notes(sent), [])

    async def test_bare_sell_all_refusal_verbatim(self):
        def setup():
            zone, room = make_world('bgE')
            char = make_character('bgE', room)
            hide_def = make_item_def('bgE', 'Animal Hide', base_value=3)
            make_vendor('bgE', room, [(hide_def, 9)])
            return char, make_owned_item(hide_def, char)
        char, hide = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all')

        lines = outputs(sent)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['text'], BARE_ALL_REFUSAL)
        exists = await sync_to_async(
            lambda: ItemInstance.objects.filter(pk=hide.pk).exists())()
        self.assertTrue(exists)

    async def test_138_bound_zero_value_junk_still_bulk_sells(self):
        # #138 regression: the guard narrows default reach, not
        # sellability — worthless non-consumable junk keeps its exit.
        def setup():
            zone, room = make_world('bgF')
            char = make_character('bgF', room)
            junk_def = make_item_def('bgF', 'Junk Scrap', base_value=0)
            make_vendor('bgF', room, [(junk_def, 9)])
            junk = make_owned_item(junk_def, char, bound=True)
            return char, junk, char.copper
        char, junk, copper_before = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all common')

        def state():
            return (ItemInstance.objects.filter(pk=junk.pk).exists(),
                    Character.objects.get(pk=char.pk).copper)
        exists, copper_after = await sync_to_async(state)()
        self.assertFalse(exists)
        self.assertEqual(copper_after, copper_before)
        self.assertEqual(self._skip_notes(sent), [])

    async def test_materials_unaffected_by_guard(self):
        def setup():
            zone, room = make_world('bgG')
            char = make_character('bgG', room)
            hide_def = make_item_def('bgG', 'Animal Hide', base_value=3)
            carapace_def = make_item_def('bgG', 'Insect Carapace',
                                         base_value=3)
            make_vendor('bgG', room, [(hide_def, 9)])
            return char, ([make_owned_item(hide_def, char) for _ in range(2)]
                          + [make_owned_item(carapace_def, char)])
        char, materials = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('all common')

        def remaining():
            return ItemInstance.objects.filter(
                pk__in=[m.pk for m in materials]).count()
        self.assertEqual(await sync_to_async(remaining)(), 0)
        self.assertEqual(self._skip_notes(sent), [])
