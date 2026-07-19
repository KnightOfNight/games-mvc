"""v20 brief 3 (#22): the authoritative command-grammar unit suite.

Implements the brief's Part A5 table (cases 1-30) plus the required
added coverage. The table is authoritative — cases may be added but
never changed. All candidates are in-memory model instances (no DB):
the resolver operates on candidate lists supplied by the commands, so
the suite exercises it exactly as the consumer does.
"""
import random
from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from apps.shyland.command_grammar import resolve, complete
from apps.shyland.models import (
    ItemDefinition, ItemInstance, NpcDefinition, NpcInstance, VendorEntry,
)

BASE_TIME = timezone.now() - timedelta(days=1)


def make_def(pk, name, item_type='material', suppress=False,
             valid_slots=None, mystery=''):
    return ItemDefinition(
        pk=pk, name=name, slug=f'def-{pk}', item_type=item_type,
        genre_tag='fantasy', suppress_mk_suffix=suppress,
        mystery_name=mystery, valid_slots=valid_slots or [],
        scaling_base=0.0, scaling_factor=0.0,
    )


def make_item(pk, defn, rarity='common', mk=1, dur=100.0, equipped=False,
              bound=False, identified=True):
    item = ItemInstance(
        pk=pk, mk_tier=mk, rarity=rarity, durability_current=dur,
        is_equipped=equipped, is_soulbound=bound, is_identified=identified,
    )
    item.definition = defn
    # Age order == pk order; ties impossible.
    item.created_at = BASE_TIME + timedelta(seconds=pk)
    return item


class GrammarFixtureMixin:
    """The Part A5 inventory fixture."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.battle_axe = make_def(1, 'Battle Axe', 'weapon',
                                  valid_slots=['MAIN_HAND'])
        cls.iron_mace = make_def(2, 'Iron Mace', 'weapon',
                                 valid_slots=['MAIN_HAND'])
        cls.healing_draught = make_def(3, 'Healing Draught', 'consumable')
        cls.animal_hide = make_def(4, 'Animal Hide', 'material')
        cls.insect_carapace = make_def(5, 'Insect Carapace', 'material')
        cls.hunting_knife = make_def(6, 'Hunting Knife', 'weapon',
                                     valid_slots=['MAIN_HAND'])
        cls.trinket_def = make_def(7, 'Odd Trinket', 'accessory',
                                   mystery='a strange trinket')
        cls.vigor_draught = make_def(8, 'Draught of Vigor', 'consumable')

        # Battle Axe Mk 1 x2 — one Uncommon 100%, one Common 60%.
        cls.axe_uncommon = make_item(101, cls.battle_axe, 'uncommon', dur=100.0)
        cls.axe_common = make_item(102, cls.battle_axe, 'common', dur=60.0)
        # Iron Mace Mk 1 — Common, equipped, bound.
        cls.mace = make_item(103, cls.iron_mace, 'common',
                             equipped=True, bound=True)
        # Healing Draught x7 (actual definition config: Mk suffix shown).
        cls.draughts = [make_item(110 + i, cls.healing_draught)
                        for i in range(7)]
        # Animal Hide x3.
        cls.hides = [make_item(120 + i, cls.animal_hide) for i in range(3)]
        # Insect Carapace x2.
        cls.carapaces = [make_item(125 + i, cls.insect_carapace)
                         for i in range(2)]
        # Hunting Knife x2 — one Common, one Rare.
        cls.knife_common = make_item(131, cls.hunting_knife, 'common')
        cls.knife_rare = make_item(132, cls.hunting_knife, 'rare')
        # One unidentified item with mystery name "a strange trinket".
        cls.trinket = make_item(141, cls.trinket_def, 'rare', identified=False)

        cls.carried = ([cls.axe_uncommon, cls.axe_common, cls.mace]
                       + cls.draughts + cls.hides + cls.carapaces
                       + [cls.knife_common, cls.knife_rare, cls.trinket])
        cls.consumables = list(cls.draughts)   # trinket is not a consumable
        cls.equipped = [cls.mace]
        cls.equippables = [i for i in cls.carried
                           if i.definition.valid_slots and not i.is_equipped]

        # Vendor stock: Healing Draught. Case 27 adds Draught of Vigor to
        # the stock (per the table's own note) — with it present, a noun
        # that prefix-matches both definitions must refuse.
        cls.entry_healing = VendorEntry(pk=1, mk_tier=1)
        cls.entry_healing.item_definition = cls.healing_draught
        cls.entry_vigor = VendorEntry(pk=2, mk_tier=1)
        cls.entry_vigor.item_definition = cls.vigor_draught
        cls.vendor_stock = [cls.entry_healing]
        cls.vendor_stock_with_vigor = [cls.entry_healing, cls.entry_vigor]

        # NPCs: cave spider + spitting spider (cases 28-30).
        cave_def = NpcDefinition(pk=1, name='cave spider')
        spit_def = NpcDefinition(pk=2, name='spitting spider')
        cls.cave_spider = NpcInstance(pk=201, mk_tier=1,
                                      vitality_current=10, vitality_max=10)
        cls.cave_spider.definition = cave_def
        cls.spitting_spider = NpcInstance(pk=202, mk_tier=1,
                                          vitality_current=10, vitality_max=10)
        cls.spitting_spider.definition = spit_def
        cls.npcs = [cls.cave_spider, cls.spitting_spider]


class AuthoritativeTableTests(GrammarFixtureMixin, SimpleTestCase):
    """The Part A5 table, case by case."""

    def test_01_sell_axe_picks_lowest_rarity(self):
        res = resolve('sell', 'axe', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.axe_common])

    def test_02_sell_full_name_with_tier(self):
        res = resolve('sell', 'battle axe mk 1', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.axe_common])

    def test_03_sell_uncommon_axe_qualifier_filter(self):
        res = resolve('sell', 'uncommon axe', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.axe_uncommon])

    def test_04_equip_axe_picks_highest_rarity(self):
        res = resolve('equip', 'axe', self.equippables)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.axe_uncommon])

    def test_05_sell_all_axes_plural_strip(self):
        res = resolve('sell', 'all axes', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), {self.axe_common, self.axe_uncommon})
        self.assertEqual(res.mode, 'all')

    def test_06_sell_2_dot_axe_second_in_stable_order(self):
        res = resolve('sell', '2.axe', self.carried)
        self.assertTrue(res.ok)
        # Stable order is age order: uncommon (pk 101) then common (pk 102).
        self.assertEqual(res.items, [self.axe_common])

    def test_07_sell_mace_only_match_is_equipped(self):
        res = resolve('sell', 'mace', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'equipped')
        self.assertEqual(res.message, "You'll have to unequip it first.")

    def test_08_unequip_mace_1_ordered_tokens(self):
        res = resolve('unequip', 'mace 1', self.equipped)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.mace])

    def test_09_use_draught(self):
        res = resolve('use', 'draught', self.consumables)
        self.assertTrue(res.ok)
        self.assertEqual(res.items[0].definition, self.healing_draught)

    def test_10_use_draughts_plural(self):
        res = resolve('use', 'draughts', self.consumables)
        self.assertTrue(res.ok)
        self.assertEqual(res.items[0].definition, self.healing_draught)

    def test_11_buy_10_draughts_all_or_nothing_quantity(self):
        res = resolve('buy', '10 draughts', self.vendor_stock)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.entry_healing])
        self.assertEqual(res.quantity, 10)

    def test_12_sell_5_hides_partial_fulfillment(self):
        # v22 brief 2 (DD §7) supersedes the v20 all-or-nothing refusal:
        # sell does the possible part and reports the shortfall via
        # `requested` — the handler prints the warm line.
        res = resolve('sell', '5 hides', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(self.hides))
        self.assertEqual(res.requested, 5)

    def test_13_sell_all_hides(self):
        res = resolve('sell', 'all hides', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(self.hides))

    def test_14_sell_all_carapaces_es_strip(self):
        res = resolve('sell', 'all carapaces', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(self.carapaces))

    def test_15_sell_knives_ves_plural_one_definition_lowest(self):
        res = resolve('sell', 'knives', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.knife_common])

    def test_16_sell_rare_knife(self):
        res = resolve('sell', 'rare knife', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.knife_rare])

    def test_17_sell_all_common_every_unequipped_common(self):
        res = resolve('sell', 'all common', self.carried)
        self.assertTrue(res.ok)
        expected = {i for i in self.carried
                    if i.rarity == 'common' and not i.is_equipped}
        self.assertEqual(set(res.items), expected)
        self.assertNotIn(self.mace, res.items)

    def test_18_bare_sell_all_refused_with_usage(self):
        res = resolve('sell', 'all', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(
            res.message,
            "Sell all of what? Try 'sell all <item>' or 'sell all <rarity>'.",
        )

    def test_19_h_d_ordered_subsequence(self):
        res = resolve('use', 'h d', self.consumables)
        self.assertTrue(res.ok)
        self.assertEqual(res.items[0].definition, self.healing_draught)

    def test_20_d_h_order_violated(self):
        res = resolve('use', 'd h', self.consumables)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'not_found')

    def test_21_rap_no_mid_word_match(self):
        res = resolve('sell', 'rap', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'not_found')

    def test_22_examine_strange_matches_mystery_name(self):
        res = resolve('examine', 'strange', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.trinket])

    def test_23_use_trinket_candidate_scoping(self):
        res = resolve('use', 'trinket', self.consumables)
        self.assertFalse(res.ok)
        self.assertEqual(res.message, "You aren't carrying that.")

    def test_24_case_insensitive(self):
        res = resolve('sell', 'HIDE', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items[0].definition, self.animal_hide)

    def test_25_epic_axe_qualifier_filters_to_empty(self):
        res = resolve('sell', 'epic axe', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'not_found')

    def test_26_common_2_dot_knife_bad_index(self):
        res = resolve('sell', 'common 2.knife', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'bad_index')

    def test_27_buy_dra_disambiguation_across_definitions(self):
        res = resolve('buy', 'dra', self.vendor_stock_with_vigor)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'ambiguous')
        self.assertIn('Healing Draught', res.message)
        self.assertIn('Draught of Vigor', res.message)

    def test_28_attack_spider_disambiguation_across_npc_definitions(self):
        res = resolve('attack', 'spider', self.npcs)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'ambiguous')
        self.assertIn('cave spider', res.message)
        self.assertIn('spitting spider', res.message)

    def test_29_attack_cave(self):
        res = resolve('attack', 'cave', self.npcs)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.cave_spider])

    def test_30_attack_all_spiders_refused(self):
        res = resolve('attack', 'all spiders', self.npcs)
        self.assertFalse(res.ok)
        self.assertEqual(res.message, 'You can only attack one target.')


class AddedCoverageTests(GrammarFixtureMixin, SimpleTestCase):
    """The brief's required extra coverage plus resolver edge cases."""

    def test_suppressed_suffix_names_carry_no_mk_tokens(self):
        ingot_def = make_def(9, 'Copper Ingot', 'material', suppress=True)
        ingot = make_item(150, ingot_def)
        res = resolve('sell', 'ingot mk', self.carried + [ingot])
        self.assertFalse(res.ok)  # no 'mk' token on a suppressed name
        res = resolve('sell', 'ingot', self.carried + [ingot])
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [ingot])

    def test_sell_uncommon_with_exactly_one_uncommon_sells_it(self):
        res = resolve('sell', 'uncommon', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.axe_uncommon])

    def test_sell_uncommon_with_two_distinct_definitions_refuses(self):
        knife_uncommon = make_item(151, self.hunting_knife, 'uncommon')
        res = resolve('sell', 'uncommon', self.carried + [knife_uncommon])
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'ambiguous')
        self.assertIn('Battle Axe', res.message)
        self.assertIn('Hunting Knife', res.message)

    def test_index_ordering_stable_across_calls_and_input_order(self):
        shuffled = list(self.carried)
        for seed in range(5):
            random.Random(seed).shuffle(shuffled)
            res = resolve('sell', '2.axe', shuffled)
            self.assertTrue(res.ok)
            self.assertEqual(res.items, [self.axe_common])

    def test_unidentified_item_never_shows_tier_token(self):
        # Mystery name tokens only: 'mk' must not match the trinket.
        res = resolve('examine', 'trinket mk', self.carried)
        self.assertFalse(res.ok)

    def test_sell_2_hides_all_or_nothing_success(self):
        res = resolve('sell', '2 hides', self.carried)
        self.assertTrue(res.ok)
        self.assertEqual(len(res.items), 2)
        self.assertEqual(res.mode, 'count')
        self.assertTrue(all(i.definition == self.animal_hide
                            for i in res.items))

    def test_loot_bare_all_allowed(self):
        contents = [make_item(160, self.animal_hide),
                    make_item(161, self.hunting_knife, 'rare')]
        res = resolve('loot', 'all', contents)
        self.assertTrue(res.ok)
        self.assertEqual(set(res.items), set(contents))

    def test_drop_all_rejected_numeric_only(self):
        # v22 brief 2 (DD §1 fn 11) supersedes the v20 bare-all sweep:
        # drop takes a numeric-only quantity; 'all' is refused with
        # teaching wording.
        res = resolve('drop', 'all', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'usage')
        self.assertEqual(res.message, "Drop how many? Try 'drop <N> <item>'.")

    def test_pickup_bare_all_allowed(self):
        ground = [make_item(170, self.animal_hide)]
        res = resolve('pickup', 'all', ground)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, ground)

    def test_all_with_noun_spanning_definitions_refuses(self):
        # 'all dra...' across two definitions is still a guess — refuse.
        contents = [make_item(180, self.healing_draught),
                    make_item(181, self.vigor_draught)]
        res = resolve('use', 'h d', contents)  # sanity: fixture intact
        self.assertTrue(res.ok)
        res = resolve('sell', 'all dra', contents)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'ambiguous')

    def test_count_with_index_refused(self):
        res = resolve('sell', '2 2.hide', self.carried)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'usage')

    def test_equip_selection_condition_tiebreak(self):
        # Same rarity: best condition wins for equip.
        worn = make_item(190, self.hunting_knife, 'common', dur=30.0)
        res = resolve('equip', 'knife',
                      [i for i in [worn, self.knife_common]
                       if not i.is_equipped])
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.knife_common])

    def test_sell_selection_damage_tiebreak(self):
        # Same rarity: most damaged sells first.
        worn = make_item(191, self.hunting_knife, 'common', dur=30.0)
        res = resolve('sell', 'knife', [worn, self.knife_common])
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [worn])

    def test_oldest_selection_for_use(self):
        res = resolve('use', 'draught', self.consumables)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.draughts[0]])

    def test_attack_no_plural_fallback(self):
        res = resolve('attack', 'spiders', [self.cave_spider])
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'not_found')

    def test_attack_index_form_retained(self):
        second_cave = NpcInstance(pk=203, mk_tier=1,
                                  vitality_current=10, vitality_max=10)
        second_cave.definition = self.cave_spider.definition
        res = resolve('attack', '2.cave', [self.cave_spider, second_cave])
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [second_cave])

    def test_buy_matches_on_tier_token(self):
        res = resolve('buy', 'healing draught mk 1', self.vendor_stock)
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [self.entry_healing])

    def test_zero_count_refused(self):
        res = resolve('sell', '0 hides', self.carried)
        self.assertFalse(res.ok)


class CompletionTests(GrammarFixtureMixin, SimpleTestCase):
    """Part G server-side completion over the same candidate scopes."""

    def test_argument_token_completion(self):
        options = complete('sell', 'ax', self.carried)
        self.assertIn('axe', options)
        self.assertNotIn('mace', options)

    def test_qualifiers_offered_at_first_position(self):
        options = complete('sell', '', self.carried)
        self.assertIn('all', options)
        self.assertIn('common', options)      # rarity present in inventory
        self.assertNotIn('epic', options)     # no epic item carried

    def test_rarity_offered_after_all(self):
        options = complete('sell', 'all ', self.carried)
        self.assertIn('common', options)
        self.assertIn('uncommon', options)

    def test_context_filtering_by_previous_tokens(self):
        options = complete('sell', 'battle ', self.carried)
        self.assertIn('axe', options)
        self.assertNotIn('hide', options)

    def test_empty_candidate_set(self):
        self.assertEqual(complete('sell', 'ax', []), [])

    def test_attack_completion_no_qualifiers(self):
        options = complete('attack', '', self.npcs)
        self.assertNotIn('all', options)
        self.assertIn('cave', options)
        self.assertIn('spider', options)
