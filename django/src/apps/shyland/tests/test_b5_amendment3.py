"""v22 Brief 5 Amendment 3 — Shortfall Visibility (#132).

Five consequence-bearing messages recategorized 'system' -> 'warn',
wording byte-identical; the sell shortfall's success voice guarded as
the deliberate exception.
"""

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase

from apps.shyland.models import (
    Character, EffectComponent, EffectDefinition, ItemInstance, VendorEntry,
)

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_vendor, make_world, outputs,
)


def msg_for(sent, text):
    return next((m for m in outputs(sent) if m['text'] == text), None)


class ShortfallWarnTests(TransactionTestCase):

    async def test_use_shortfall_is_warn(self):
        def setup():
            zone, room = make_world('svA')
            char = make_character('svA', room)
            Character.objects.filter(pk=char.pk).update(
                vitality_current=10, vitality_max=1000)
            heal = EffectDefinition.objects.create(
                name='svA Heal', slug='sva-heal')
            EffectComponent.objects.create(
                definition=heal, component_type='restore_vitality',
                magnitude_base=5.0, magnitude_scaling=0.0,
                duration_base=0.0, duration_scaling=0.0,
            )
            draught = make_item_def('svA', 'Healing Draught', 'consumable',
                                    effect=heal)
            for _ in range(2):
                make_owned_item(draught, char)
            return Character.objects.select_related('user').get(pk=char.pk)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('5 healing draught')
        msg = msg_for(sent, 'You only had 2.')
        self.assertIsNotNone(msg, [m['text'] for m in outputs(sent)])
        self.assertEqual(msg['category'], 'warn')

    async def test_drop_shortfall_is_warn(self):
        def setup():
            zone, room = make_world('svB')
            char = make_character('svB', room)
            hide = make_item_def('svB', 'Animal Hide')
            for _ in range(2):
                make_owned_item(hide, char)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_drop('5 hide')
        msg = msg_for(sent, 'You only had 2.')
        self.assertIsNotNone(msg, [m['text'] for m in outputs(sent)])
        self.assertEqual(msg['category'], 'warn')

    async def test_pickup_shortfall_is_warn(self):
        def setup():
            zone, room = make_world('svC')
            char = make_character('svC', room)
            hide = make_item_def('svC', 'Animal Hide')
            for _ in range(2):
                ItemInstance.objects.create(
                    definition=hide, current_room=room, mk_tier=1,
                    rarity='common', durability_current=100.0,
                    is_identified=True,
                )
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('5 hide')
        msg = msg_for(sent, 'There were only 2 here.')
        self.assertIsNotNone(msg, [m['text'] for m in outputs(sent)])
        self.assertEqual(msg['category'], 'warn')

    async def test_buy_shortfall_is_warn(self):
        def setup():
            zone, room = make_world('svD')
            char = make_character('svD', room)
            Character.objects.filter(pk=char.pk).update(copper=1000)
            hide = make_item_def('svD', 'Animal Hide', base_value=4)
            make_vendor('svD', room, [(hide, 10)])
            VendorEntry.objects.filter(item_definition=hide).update(
                stock_limit=2)
            return Character.objects.select_related('user').get(pk=char.pk)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_buy('5 hide')
        msg = msg_for(sent, 'They only had 2.')
        self.assertIsNotNone(msg, [m['text'] for m in outputs(sent)])
        self.assertEqual(msg['category'], 'warn')

    async def test_nothing_happens_is_warn(self):
        def setup():
            zone, room = make_world('svE')
            char = make_character('svE', room)
            dud = make_item_def('svE', 'Inert Tonic', 'consumable')
            make_owned_item(dud, char)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('tonic')
        msg = msg_for(sent, 'Nothing happens.')
        self.assertIsNotNone(msg, [m['text'] for m in outputs(sent)])
        self.assertEqual(msg['category'], 'warn')

    async def test_sell_shortfall_stays_success(self):
        # The ruled exception: the vendor happily takes what you have.
        def setup():
            zone, room = make_world('svF')
            char = make_character('svF', room)
            hide = make_item_def('svF', 'Animal Hide', base_value=4)
            for _ in range(3):
                make_owned_item(hide, char)
            make_vendor('svF', room, [(hide, 10)])
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('5 hide')
        msg = msg_for(sent, 'You only had 3 — the vendor was happy to take them.')
        self.assertIsNotNone(msg, [m['text'] for m in outputs(sent)])
        self.assertEqual(msg['category'], 'success')
