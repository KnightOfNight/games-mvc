"""V25.13 Brief 1 (#275, #319): over-capacity legibility.

Direction B: the over-capacity state is legal and legible. Unequipping
(or auto-swap-displacing) stat-granting gear may drop carry capacity
below current load — the action succeeds and warns, never refuses. The
stranding warn fires whenever a completed gear change leaves the
character strictly over capacity; the four acquisition gates (pickup,
buy, single-corpse loot, sweep loot) say "You're over your carry limit."
when strictly over, keeping their existing strings at ordinary fullness.
Folded in per #319: pickup and buy count load on the unequipped-only
basis (get_carry_counts) the rest of the game uses; the all-items
get_carry_capacity outlier is retired. The bag guard is byte-identical.
"""

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase

from apps.shyland.models import ItemDefinition, ItemInstance

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_vendor, make_world, outputs,
)
from .test_gear_combat import equip_gear, make_gear_def
from .test_v245_bare_loot import make_corpse, make_npc_def


STRANDING_WARN = (
    "You're over your carry limit ({current}/{max} items) "
    "— you can't pick up, loot, or buy anything until you're under it."
)
OVER_LIMIT_REFUSAL = "You're over your carry limit. ({current}/{max} items)"


def warn_texts(sent):
    return [m['text'] for m in outputs(sent) if m['category'] == 'warn']


def add_fillers(prefix, char, count):
    defn = make_item_def(prefix, f'{prefix} Pebble')
    for _ in range(count):
        make_owned_item(defn, char)
    return defn


def strand_fixture(prefix, fillers=12):
    """A character one unequip away from stranding: STR 1 (naked capacity
    10), +2 STR gauntlets equipped (capacity 30), 12 unequipped fillers.
    Unequipping the gauntlets lands at 13/10 — strictly over."""
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    char.stat_str = 1
    char.save()
    gaunt_def = make_gear_def(prefix, 'Power Gauntlets', slot='HANDS')
    gauntlets = equip_gear(gaunt_def, char, 'HANDS',
                           primary=[{'stat': 'str', 'value': 2}])
    add_fillers(prefix, char, fillers)
    return zone, room, char, gauntlets


def over_fixture(prefix, count=13):
    """A character already strictly over: STR 1 (capacity 10), no gear,
    13 unequipped fillers — 13/10."""
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    char.stat_str = 1
    char.copper = 1_000
    char.save()
    add_fillers(prefix, char, count)
    return zone, room, char


class StrandingWarnTests(TransactionTestCase):
    """Brief §3 Step 4: the warn at the moment of stranding."""

    async def test_stranding_unequip_succeeds_and_warns(self):
        zone, room, char, gauntlets = await sync_to_async(strand_fixture)('sw1')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_unequip('gauntlets')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('You unequip the Power Gauntlets Mk 1.', texts)
        self.assertIn(STRANDING_WARN.format(current=13, max=10),
                      warn_texts(sent))
        current, max_carry = await consumer.get_carry_counts(char)
        self.assertGreater(current, max_carry)

    async def test_stranding_auto_swap_warns_with_swap_sentence(self):
        zone, room, char, gauntlets = await sync_to_async(strand_fixture)('sw2')

        def add_gloves():
            defn = make_gear_def('sw2', 'Plain Gloves', slot='HANDS')
            return make_owned_item(defn, char)
        await sync_to_async(add_gloves)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_equip('gloves')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn(
            'You equip the Plain Gloves Mk 1, '
            'replacing the Power Gauntlets Mk 1.',
            texts)
        # 12 fillers + the displaced gauntlets unequipped; capacity back
        # to the naked 10.
        self.assertIn(STRANDING_WARN.format(current=13, max=10),
                      warn_texts(sent))

    async def test_unequip_landing_under_capacity_no_warn(self):
        def setup():
            zone, room = make_world('sw3')
            char = make_character('sw3', room)
            char.stat_str = 1
            char.save()
            defn = make_gear_def('sw3', 'Power Gauntlets', slot='HANDS')
            equip_gear(defn, char, 'HANDS',
                       primary=[{'stat': 'str', 'value': 2}])
            add_fillers('sw3', char, 2)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_unequip('gauntlets')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('You unequip the Power Gauntlets Mk 1.', texts)
        self.assertFalse(
            [t for t in texts if 'over your carry limit' in t])


class OverLimitRefusalTests(TransactionTestCase):
    """Brief §3 Step 3: the honest refusal at each of the four sites."""

    async def test_pickup_refuses_with_over_limit_line(self):
        zone, room, char = await sync_to_async(over_fixture)('or1')

        def add_room_item():
            defn = make_item_def('or1', 'or1 Fang')
            return ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=True,
            )
        await sync_to_async(add_room_item)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('fang')
        self.assertIn(OVER_LIMIT_REFUSAL.format(current=13, max=10),
                      warn_texts(sent))

    async def test_buy_refuses_with_over_limit_line(self):
        zone, room, char = await sync_to_async(over_fixture)('or2')

        def add_vendor():
            draught = make_item_def('or2', 'Healing Draught', 'consumable')
            return make_vendor('or2', room, [(draught, 9)])
        await sync_to_async(add_vendor)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_buy('healing draught')
        self.assertIn(OVER_LIMIT_REFUSAL.format(current=13, max=10),
                      warn_texts(sent))

    async def test_single_corpse_loot_refuses_with_over_limit_line(self):
        zone, room, char = await sync_to_async(over_fixture)('or3')

        def add_corpse():
            npc_def = make_npc_def('or3', 'or3 boar')
            corpse = make_corpse(npc_def, room, char)
            fang = make_item_def('or3', 'or3 Fang')
            ItemInstance.objects.create(
                definition=fang, corpse=corpse, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
        await sync_to_async(add_corpse)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_loot('boar')
        self.assertIn(OVER_LIMIT_REFUSAL.format(current=13, max=10),
                      warn_texts(sent))

    async def test_sweep_loot_refuses_with_over_limit_line(self):
        zone, room, char = await sync_to_async(over_fixture)('or4')

        def add_corpse():
            npc_def = make_npc_def('or4', 'or4 boar')
            corpse = make_corpse(npc_def, room, char)
            fang = make_item_def('or4', 'or4 Fang')
            ItemInstance.objects.create(
                definition=fang, corpse=corpse, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
        await sync_to_async(add_corpse)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_loot('all')
        self.assertIn(OVER_LIMIT_REFUSAL.format(current=13, max=10),
                      warn_texts(sent))


class ExactFullTests(TransactionTestCase):
    """Brief §5.5: at exactly full the existing strings are unchanged."""

    async def test_pickup_at_exactly_full_keeps_existing_string(self):
        zone, room, char = await sync_to_async(over_fixture)('xf1', count=10)

        def add_room_item():
            defn = make_item_def('xf1', 'xf1 Fang')
            ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=True,
            )
        await sync_to_async(add_room_item)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('fang')
        warns = warn_texts(sent)
        self.assertIn("You can't carry any more. (10/10 items)", warns)
        self.assertFalse([t for t in warns if 'over your carry limit' in t])

    async def test_buy_at_exactly_full_keeps_existing_string(self):
        zone, room, char = await sync_to_async(over_fixture)('xf2', count=10)

        def add_vendor():
            draught = make_item_def('xf2', 'Healing Draught', 'consumable')
            make_vendor('xf2', room, [(draught, 9)])
        await sync_to_async(add_vendor)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_buy('healing draught')
        warns = warn_texts(sent)
        self.assertIn("You can't carry any more. (10/10 items)", warns)
        self.assertFalse([t for t in warns if 'over your carry limit' in t])


class CountBasisTests(TransactionTestCase):
    """Brief §5.6 (#319): equipped items no longer count against pickup."""

    async def test_pickup_succeeds_when_only_all_items_count_would_refuse(self):
        # U = 8 unequipped, E = 3 equipped, M = 10: U < M <= U + E. The
        # retired all-items basis (11 >= 10) refused; the unequipped-only
        # basis (8 < 10) admits the pickup.
        def setup():
            zone, room = make_world('cb1')
            char = make_character('cb1', room)
            char.stat_str = 1
            char.save()
            add_fillers('cb1', char, 8)
            ring_def = make_gear_def('cb1', 'Plain Band', slot='RING')
            for slot in ('RING', 'RING', 'NECK'):
                equip_gear(ring_def, char, slot)
            defn = make_item_def('cb1', 'cb1 Fang')
            item = ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=True,
            )
            return char, item
        char, item = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('fang')
        self.assertFalse(
            [t for t in warn_texts(sent) if "carry" in t])
        owner_id = await sync_to_async(
            lambda: ItemInstance.objects.get(pk=item.pk).owner_id)()
        self.assertEqual(owner_id, char.pk)


class BagGuardRegressionTests(TransactionTestCase):
    """Brief §5.7: the bag guard is byte-identical — refuse, no warn."""

    async def test_stranding_bag_unequip_still_refuses(self):
        def setup():
            zone, room = make_world('bg1')
            char = make_character('bg1', room)
            char.stat_str = 1
            char.save()
            bag_def = ItemDefinition.objects.create(
                name='Canvas Sack', slug='bg1-canvas-sack', item_type='bag',
                genre_tag='fantasy', valid_slots=['BACK'],
                scaling_base=0.0, scaling_factor=0.0, base_value=1,
                carry_pct_base=100, carry_pct_per_mk=0,
                # v25.12 (#311): explicit non-wearing posture — bags
                # never wear.
                takes_durability_loss=False, durability_table=[],
            )
            # Capacity 20 with the bag, 10 without; 15 carried items
            # strand without it.
            ItemInstance.objects.create(
                definition=bag_def, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
                is_equipped=True, equipped_slot='BACK',
            )
            add_fillers('bg1', char, 15)
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_unequip('sack')
        warns = warn_texts(sent)
        self.assertIn(
            "You're carrying too many items to remove your Canvas Sack.",
            warns)
        self.assertFalse([t for t in warns if 'over your carry limit' in t])
        still_equipped = await sync_to_async(
            lambda: ItemInstance.objects.filter(
                owner=char, is_equipped=True,
                definition__item_type='bag').exists())()
        self.assertTrue(still_equipped)


class RecoveryTests(TransactionTestCase):
    """Brief §5.8: re-equipping from the over state clears it."""

    async def test_reequip_lands_under_no_warn_and_acquisition_returns(self):
        zone, room, char, gauntlets = await sync_to_async(strand_fixture)('rc1')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_unequip('gauntlets')
        self.assertIn(STRANDING_WARN.format(current=13, max=10),
                      warn_texts(sent))

        # Re-equip: 12 unequipped against capacity 30 — no warn.
        sent.clear()
        await consumer.cmd_equip('gauntlets')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('You equip the Power Gauntlets Mk 1.', texts)
        self.assertFalse(
            [t for t in texts if 'over your carry limit' in t])

        # Acquisition works again.
        def add_room_item():
            defn = make_item_def('rc1', 'rc1 Fang')
            return ItemInstance.objects.create(
                definition=defn, current_room=room, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=True,
            )
        item = await sync_to_async(add_room_item)()
        sent.clear()
        await consumer.cmd_pickup('fang')
        self.assertFalse(
            [t for t in warn_texts(sent) if 'carry' in t])
        owner_id = await sync_to_async(
            lambda: ItemInstance.objects.get(pk=item.pk).owner_id)()
        self.assertEqual(owner_id, char.pk)
