"""v22 brief 2 amendment 5: transactional aggregation (×N).

buy/sell/drop/pickup aggregate N>1 to one count-form line per item
definition (a transaction is one act); use/repair/loot stay per-line
(each iteration is its own news)."""

from asgiref.sync import sync_to_async
from django.test import TransactionTestCase

from apps.shyland.models import Character, ItemInstance
from apps.shyland.tests.test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_vendor, make_world, outputs,
)


def floor_item(defn, room):
    return ItemInstance.objects.create(
        definition=defn, current_room=room, mk_tier=1, rarity='common',
        durability_current=100.0, is_identified=True,
    )


class AggregateSentenceTests(TransactionTestCase):

    async def test_buy_aggregate_total_price_no_article(self):
        zone, room = await sync_to_async(make_world)('agA')

        def setup():
            char = make_character('agA', room)
            Character.objects.filter(pk=char.pk).update(copper=10_000)
            draught = make_item_def('agA', 'Healing Draught', 'consumable')
            make_vendor('agA', room, [(draught, 9)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_buy('3 healing draught')
        texts = [m['text'] for m in outputs(sent)]
        buys = [t for t in texts if t.startswith('You buy')]
        self.assertEqual(len(buys), 1)
        self.assertTrue(buys[0].startswith('You buy Healing Draught Mk 1 ×3 for'))
        # Total, not the 9-copper unit, through the tier formatter.
        self.assertIn('2 silvers, 7 coppers', buys[0])
        self.assertNotIn('the Healing', buys[0])

    async def test_buy_single_sentence_unchanged(self):
        zone, room = await sync_to_async(make_world)('agB')

        def setup():
            char = make_character('agB', room)
            Character.objects.filter(pk=char.pk).update(copper=100)
            mace = make_item_def('agB', 'Iron Mace', 'weapon', base_value=9)
            make_vendor('agB', room, [(mace, 9)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_buy('iron mace')
        texts = [m['text'] for m in outputs(sent)]
        self.assertTrue(any(
            t.startswith('You buy the Iron Mace Mk 1 for') for t in texts))

    async def test_sell_aggregate_total(self):
        zone, room = await sync_to_async(make_world)('agC')

        def setup():
            char = make_character('agC', room)
            hide = make_item_def('agC', 'Animal Hide', base_value=4)
            for _ in range(3):
                make_owned_item(hide, char)
            make_vendor('agC', room, [(hide, 10)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('3 hide')
        texts = [m['text'] for m in outputs(sent)]
        sells = [t for t in texts if t.startswith('You sell')]
        self.assertEqual(len(sells), 1)
        self.assertTrue(sells[0].startswith('You sell Animal Hide Mk 1 ×3 for'))

    async def test_drop_aggregate_names_captured_before_reveil(self):
        zone, room = await sync_to_async(make_world)('agD')

        def setup():
            char = make_character('agD', room)
            axe = make_item_def('agD', 'Battle Axe', 'weapon', base_value=5)
            for _ in range(2):
                make_owned_item(axe, char)
            return char
        char = await sync_to_async(setup)()

        # drop 2 axes -> one aggregate line, named BEFORE the transfer
        # re-veils identification (#80).
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_drop('2 battle axe')
        texts = [m['text'] for m in outputs(sent)]
        drops = [t for t in texts if t.startswith('You drop')]
        self.assertEqual(drops, ['You drop Battle Axe Mk 1 ×2.'])

    async def test_pickup_mixed_litter_per_definition_in_floor_order(self):
        zone, room = await sync_to_async(make_world)('agF')

        def setup():
            char = make_character('agF', room)
            hide = make_item_def('agF', 'Animal Hide')
            axe = make_item_def('agF', 'Battle Axe', 'weapon', base_value=5)
            club = make_item_def('agF', 'Oak Club', 'weapon', base_value=2)
            # Floor litter in mint order: two hides, three axes, one club.
            floor_item(hide, room)
            floor_item(hide, room)
            for _ in range(3):
                floor_item(axe, room)
            floor_item(club, room)
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('all')
        picks = [m for m in outputs(sent) if m['text'].startswith('You pick up')]
        self.assertEqual([m['text'] for m in picks], [
            'You pick up Animal Hide Mk 1 ×2.',
            'You pick up Battle Axe Mk 1 ×3.',
            'You pick up the Oak Club Mk 1.',   # a single stays singular
        ])
        for m in picks:
            self.assertEqual(m['category'], 'reward')

    async def test_pickup_single_stays_singular(self):
        zone, room = await sync_to_async(make_world)('agE')

        def setup():
            char = make_character('agE', room)
            hide = make_item_def('agE', 'Animal Hide')
            floor_item(hide, room)
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('hide')
        msgs = [m for m in outputs(sent) if m['text'].startswith('You pick up')]
        self.assertEqual(msgs[0]['text'], 'You pick up the Animal Hide Mk 1.')
        self.assertEqual(msgs[0]['category'], 'reward')
