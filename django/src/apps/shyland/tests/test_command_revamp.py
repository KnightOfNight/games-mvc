"""v22 brief 2 (#111 et al.): the B2 command revamp.

Chart conformance (DD §1), the three-layer response doctrine (§3), the
state-gating matrix (§5), success sentences (§6), partial fulfillment
(§7), resolution pools and the player/NPC name invariant (§8, #122),
settings standards (§10), say and crit prose (§13), and completion
literals. Grammar cases run DB-free on in-memory instances; handler and
engine cases run over the real DB with stubbed delivery."""

import asyncio
import uuid

from asgiref.sync import sync_to_async
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.command_grammar import complete as grammar_complete, resolve
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.forms import CharacterCreationForm
from apps.shyland.models import (
    Archetype, Character, CombatSession, Corpse, DialogueEntry,
    DialogueResponse, EffectComponent, EffectDefinition, ItemDefinition,
    ItemInstance, NpcDefinition, NpcInstance, Origin, PendingDialogueResponse,
    Room, VendorEntry, Zone,
)

BASE_TIME = timezone.now() - timedelta(days=1)


# ----------------------------------------------------------------------
# In-memory grammar fixtures (no DB)
# ----------------------------------------------------------------------

def mem_def(pk, name, item_type='material'):
    return ItemDefinition(
        pk=pk, name=name, slug=f'memdef-{pk}', item_type=item_type,
        genre_tag='fantasy', valid_slots=[],
        scaling_base=0.0, scaling_factor=0.0,
    )


def mem_item(pk, defn, rarity='common', bound=False):
    item = ItemInstance(
        pk=pk, mk_tier=1, rarity=rarity, durability_current=100.0,
        is_equipped=False, is_soulbound=bound, is_identified=True,
    )
    item.definition = defn
    item.created_at = BASE_TIME + timedelta(seconds=pk)
    return item


class GrammarChartV22Tests(SimpleTestCase):
    """DD §1 chart deltas at the resolver layer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.draught_def = mem_def(1, 'Healing Draught', 'consumable')
        cls.draughts = [mem_item(10 + i, cls.draught_def) for i in range(2)]
        cls.hide_def = mem_def(2, 'Animal Hide')
        cls.hides = [mem_item(20 + i, cls.hide_def) for i in range(3)]
        cls.entry = VendorEntry(pk=1, mk_tier=1)
        cls.entry.item_definition = cls.draught_def

    def test_use_numeric_quantity_accepted(self):
        # #65: 'use 3 healing draught' is legal; partial (DD §7) does the
        # possible part when fewer exist.
        res = resolve('use', '2 draught', self.draughts)
        self.assertTrue(res.ok)
        self.assertEqual(len(res.items), 2)
        res = resolve('use', '3 draught', self.draughts)
        self.assertTrue(res.ok)
        self.assertEqual(len(res.items), 2)
        self.assertEqual(res.requested, 3)

    def test_use_all_rejected(self):
        res = resolve('use', 'all draught', self.draughts)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'usage')
        self.assertEqual(res.message, "Use how many? Try 'use <N> <item>'.")

    def test_buy_all_rejected(self):
        res = resolve('buy', 'all draught', [self.entry])
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'usage')
        self.assertEqual(res.message, "Buy how many? Try 'buy <N> <item>'.")

    def test_drop_all_with_noun_rejected(self):
        res = resolve('drop', 'all hide', self.hides)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'usage')

    def test_pickup_bare_numeric_names_its_target(self):
        # Footnote 13: '<verb> <N> what?'
        res = resolve('pickup', '3', self.hides)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'bare_numeric')
        self.assertEqual(res.message, 'pickup 3 what?')

    def test_sell_bare_all_blocked_teaches_the_noun_form(self):
        # Footnote 17: warn-layer refusal (code 'bare_all').
        res = resolve('sell', 'all', self.hides)
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'bare_all')
        self.assertIn("Sell all of what?", res.message)

    def test_sell_partial_carries_requested(self):
        res = resolve('sell', '5 hide', self.hides)
        self.assertTrue(res.ok)
        self.assertEqual(len(res.items), 3)
        self.assertEqual(res.requested, 5)

    def test_drop_partial_carries_requested(self):
        res = resolve('drop', '5 hide', self.hides)
        self.assertTrue(res.ok)
        self.assertEqual(len(res.items), 3)
        self.assertEqual(res.requested, 5)


class RefusalLayerTests(SimpleTestCase):
    """DD §3: resolver refusal codes map to their response layer."""

    def _res(self, error):
        from apps.shyland.command_grammar import Resolution
        return Resolution(ok=False, error=error)

    def test_syntax_shapes_are_cli_errors(self):
        for code in ('usage', 'no_multi', 'bare_numeric'):
            self.assertEqual(
                SkylandConsumer._refusal_category(self._res(code)), 'error')

    def test_world_shapes_are_warn(self):
        for code in ('not_found', 'bad_index', 'too_few', 'ambiguous',
                     'equipped', 'bare_all'):
            self.assertEqual(
                SkylandConsumer._refusal_category(self._res(code)), 'warn')


class CompletionLiteralTests(SimpleTestCase):
    """DD §8 completion: pools plus literals, per position (#67)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.axe_def = mem_def(3, 'Battle Axe', 'weapon')
        cls.axes = [mem_item(30, cls.axe_def)]

    def test_equip_completes_inventory_names(self):
        options = grammar_complete('equip', 'ax', self.axes)
        self.assertIn('axe', options)

    def test_all_offered_where_legal(self):
        self.assertIn('all', grammar_complete('sell', '', self.axes))
        self.assertIn('all', grammar_complete('pickup', '', self.axes))

    def test_all_withheld_where_numeric_only(self):
        self.assertNotIn('all', grammar_complete('drop', '', self.axes))
        self.assertNotIn('all', grammar_complete('use', '', self.axes))
        self.assertNotIn('all', grammar_complete('buy', '', self.axes))

    def test_settings_complete_the_six_words(self):
        options = SkylandConsumer._complete_words(
            '', sorted(SkylandConsumer.SETTING_WORDS), first_only=True)
        self.assertEqual(options, ['false', 'no', 'off', 'on', 'true', 'yes'])
        options = SkylandConsumer._complete_words(
            'y', sorted(SkylandConsumer.SETTING_WORDS), first_only=True)
        self.assertEqual(options, ['yes'])

    def test_spend_completes_all_and_stats_then_stats(self):
        consumer = SkylandConsumer()
        first = consumer._complete_spend('')
        self.assertIn('all', first)
        self.assertIn('dex', first)
        second = consumer._complete_spend('2 ')
        self.assertIn('dex', second)
        self.assertNotIn('all', second)


class PromptGateTests(SimpleTestCase):
    """DD §1 fn 10: the standard bare-invocation prompt, DB-free verbs."""

    def _consumer(self, sent):
        consumer = SkylandConsumer()
        consumer._character_is_dying = False

        async def fake_send_json(content, close=False):
            sent.append(content)
        consumer.send_json = fake_send_json
        return consumer

    def _bare(self, verb):
        sent = []
        consumer = self._consumer(sent)
        asyncio.run(consumer._dispatch(verb, ''))
        return sent

    def test_bare_attack_prompts(self):
        sent = self._bare('attack')
        self.assertEqual(sent[-1]['category'], 'error')
        self.assertEqual(sent[-1]['text'], 'What do you want to attack?')

    def test_alias_prompts_with_canonical_verb(self):
        sent = self._bare('k')
        self.assertEqual(sent[-1]['text'], 'What do you want to attack?')

    def test_bare_say_prompts(self):
        sent = self._bare('say')
        self.assertEqual(sent[-1]['category'], 'error')
        self.assertEqual(sent[-1]['text'], 'What do you want to say?')

    def test_bare_spend_prompts(self):
        sent = self._bare('spend')
        self.assertEqual(sent[-1]['text'], 'What do you want to spend?')


# ----------------------------------------------------------------------
# DB fixtures
# ----------------------------------------------------------------------

def make_world(prefix):
    zone = Zone.objects.create(
        name=f'{prefix} Zone', slug=f'{prefix}-zone', genre_tone='Test',
        danger_level='beginner', description='A test zone.',
    )
    room = Room.objects.create(
        zone=zone, name=f'{prefix} Room',
        description='Long.', brief_description='Brief.',
        coord_x=0, coord_y=0,
    )
    return zone, room


def make_character(prefix, room):
    user = User.objects.create_user(username=f'{prefix}_user', password='x')
    origin = Origin.objects.create(
        name=f'{prefix} Origin', slug=f'{prefix}-origin',
        acuity_baseline=1.0, acuity_band_low=0.8, acuity_band_high=1.2,
    )
    archetype = Archetype.objects.create(
        name=f'{prefix} Archetype', slug=f'{prefix}-archetype',
        primary_stat_1='str', primary_stat_2='dex',
    )
    return Character.objects.create(
        user=user, name=f'{prefix} Char',
        origin=origin, archetype=archetype,
        current_room=room, recall_room=room,
    )


def make_item_def(prefix, name, item_type='material', base_value=1,
                  effect=None, takes_durability=False):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type=item_type, genre_tag='fantasy', valid_slots=[],
        scaling_base=0.0, scaling_factor=0.0, base_value=base_value,
        effect=effect, takes_durability_loss=takes_durability,
    )


def make_owned_item(defn, char, bound=False):
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=1, rarity='common',
        durability_current=100.0, is_identified=True, is_soulbound=bound,
    )


def make_vendor(prefix, room, stock_defs):
    definition = NpcDefinition.objects.create(
        name=f'{prefix} Trader', slug=f'{prefix}-trader',
        description='A test vendor.', genre_tag='fantasy',
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    npc = NpcInstance.objects.create(
        definition=definition, current_room=room, spawn_room=room,
        vitality_current=10, vitality_max=10,
    )
    for item_def, price in stock_defs:
        VendorEntry.objects.create(
            npc_definition=definition, item_definition=item_def,
            mk_tier=1, price=price,
        )
    return npc


def make_stub_consumer(character, sent):
    consumer = SkylandConsumer()
    consumer.character = character
    consumer.character_pk = character.pk
    consumer._character_is_dying = character.is_dying
    consumer.room_group = f'room_{character.current_room_id}'
    consumer.channel_name = 'test-channel'
    consumer.scope = {'user': character.user}

    async def fake_send_json(content, close=False):
        sent.append(content)
    consumer.send_json = fake_send_json

    class DummyLayer:
        def __init__(self):
            self.events = []

        async def group_send(self, group, event):
            self.events.append((group, event))

        async def group_add(self, *args):
            pass

        async def group_discard(self, *args):
            pass

    consumer.channel_layer = DummyLayer()
    return consumer


def outputs(sent):
    return [m for m in sent if m.get('type') == 'output' and 'text' in m]


class StateMatrixTests(TransactionTestCase):
    """DD §5: the combat and dying gates, and quit's combat survival."""

    def _combat(self, char, room, prefix='sm'):
        definition = NpcDefinition.objects.create(
            name=f'{prefix} snarler', slug=f'{prefix}-snarler',
            description='x', genre_tag='fantasy', is_aggressive=True,
            base_vitality=10, base_str=1, base_dex=1, base_end=1,
            base_int=1, base_wis=1, base_per=1,
        )
        npc = NpcInstance.objects.create(
            definition=definition, current_room=room, spawn_room=room,
            vitality_current=10, vitality_max=10,
        )
        session = CombatSession.objects.create(
            room=room, last_tick_at=timezone.now(),
        )
        session.characters.add(char)
        session.npcs.add(npc)
        return session

    async def test_combat_refuses_the_blocked_set_warn(self):
        zone, room = await sync_to_async(make_world)('smA')
        char = await sync_to_async(make_character)('smA', room)
        await sync_to_async(self._combat)(char, room, 'smA')
        for verb in ('loot', 'buy', 'sell', 'equip', 'pickup', 'drop',
                     'unequip', 'repair', 'travel', 'north'):
            sent = []
            consumer = make_stub_consumer(char, sent)
            await consumer._dispatch(verb, 'anything')
            self.assertEqual(len(outputs(sent)), 1, verb)
            self.assertEqual(outputs(sent)[0]['category'], 'warn', verb)

    async def test_combat_allows_examine_and_stats(self):
        zone, room = await sync_to_async(make_world)('smB')
        char = await sync_to_async(make_character)('smB', room)
        await sync_to_async(self._combat)(char, room, 'smB')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('stats', '')
        self.assertTrue(any(m.get('category') == 'report' for m in sent))
        sent2 = []
        consumer2 = make_stub_consumer(char, sent2)
        # examine resolves nothing but must NOT be state-refused: the
        # response is a resolution miss, not the combat refusal.
        await consumer2._dispatch('examine', 'nonexistent thing')
        self.assertTrue(outputs(sent2))
        self.assertNotIn('fight', outputs(sent2)[0]['text'])

    async def test_dying_gate_allows_and_refuses_per_matrix(self):
        zone, room = await sync_to_async(make_world)('smC')
        char = await sync_to_async(make_character)('smC', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer._character_is_dying = True
        # Refused: pickup (warn), with the echo line first.
        await consumer.receive_json({'text': 'pickup hide'})
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'echo')
        self.assertEqual(msgs[1]['category'], 'warn')
        self.assertIn('dying', msgs[1]['text'])
        # Allowed: an information command dispatches (stats renders).
        sent2 = []
        consumer2 = make_stub_consumer(char, sent2)
        consumer2._character_is_dying = True
        await consumer2.receive_json({'text': 'stats'})
        self.assertTrue(any(m.get('category') == 'report' for m in sent2))

    async def test_quit_in_combat_leaves_the_session_live(self):
        zone, room = await sync_to_async(make_world)('smD')
        char = await sync_to_async(make_character)('smD', room)
        session = await sync_to_async(self._combat)(char, room, 'smD')
        sent = []
        consumer = make_stub_consumer(char, sent)
        closed = []

        async def fake_close(code=None):
            closed.append(True)
        consumer.close = fake_close

        await consumer._dispatch('quit', '')
        self.assertTrue(closed)

        def session_active():
            session.refresh_from_db()
            return session.is_active
        self.assertTrue(await sync_to_async(session_active)())


class SellDropPickupTests(TransactionTestCase):
    """DD §6/§7/§8: shortfalls, bound-drop, capacity, sentences."""

    async def test_sell_shortfall_sells_and_reports_verbatim(self):
        zone, room = await sync_to_async(make_world)('sd')

        def setup():
            char = make_character('sd', room)
            hide = make_item_def('sd', 'Animal Hide', base_value=4)
            for _ in range(3):
                make_owned_item(hide, char)
            make_vendor('sd', room, [(hide, 10)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_sell('5 hide')
        texts = [m['text'] for m in outputs(sent)]
        # v22 B2 amendment 5: the sale aggregates to one count-form line
        # with the actual count, after the warm shortfall line.
        self.assertIn('You only had 3 — the vendor was happy to take them.', texts)
        aggregate = [t for t in texts if t.startswith('You sell Animal Hide Mk 1 ×3')]
        self.assertEqual(len(aggregate), 1)

    async def test_drop_bound_refused_warn_and_excluded_from_pool(self):
        zone, room = await sync_to_async(make_world)('db')

        def setup():
            char = make_character('db', room)
            ring = make_item_def('db', 'Copper Ring', base_value=2)
            make_owned_item(ring, char, bound=True)
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_drop('ring')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertIn('bound to you and cannot be dropped', msgs[0]['text'])

    async def test_pickup_at_capacity_fails_outright_warn(self):
        zone, room = await sync_to_async(make_world)('pc')

        def setup():
            char = make_character('pc', room)
            Character.objects.filter(pk=char.pk).update(stat_str=0)
            char.stat_str = 0
            hide = make_item_def('pc', 'Animal Hide')
            ItemInstance.objects.create(
                definition=hide, current_room=room, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('hide')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertIn("can't carry any more", msgs[0]['text'])

    async def test_pickup_success_line_is_loot_colored(self):
        zone, room = await sync_to_async(make_world)('pl')

        def setup():
            char = make_character('pl', room)
            hide = make_item_def('pl', 'Animal Hide')
            ItemInstance.objects.create(
                definition=hide, current_room=room, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_pickup('hide')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'reward')
        self.assertEqual(msgs[0]['text'], 'You pick up the Animal Hide Mk 1.')


class PoolTests(TransactionTestCase):
    """DD §8: examine's union, use's scope, nearest-wins."""

    async def test_examine_resolves_vendor_stock_and_npc(self):
        zone, room = await sync_to_async(make_world)('px')

        def setup():
            char = make_character('px', room)
            sword = make_item_def('px', 'Iron Sword', base_value=9)
            make_vendor('px', room, [(sword, 12)])
            return char
        char = await sync_to_async(setup)()

        # Vendor-stock item (the old vendor-examine gap).
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_examine('iron sword')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'report')
        self.assertIn('Iron Sword', msgs[0]['text'])

        # NPC (#96 by extension).
        sent2 = []
        consumer2 = make_stub_consumer(char, sent2)
        await consumer2.cmd_examine('trader')
        msgs2 = outputs(sent2)
        self.assertEqual(msgs2[0]['category'], 'report')
        self.assertIn('A test vendor.', msgs2[0]['text'])

    async def test_use_cannot_resolve_vendor_stock(self):
        zone, room = await sync_to_async(make_world)('pu')

        def setup():
            char = make_character('pu', room)
            draught = make_item_def('pu', 'Healing Draught', 'consumable')
            make_vendor('pu', room, [(draught, 5)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(msgs[0]['text'], "You aren't carrying that.")

    async def test_nearest_wins_inventory_before_vendor(self):
        zone, room = await sync_to_async(make_world)('pn')

        def setup():
            char = make_character('pn', room)
            sword = make_item_def('pn', 'Iron Sword', base_value=9,
                                  takes_durability=True)
            mine = make_owned_item(sword, char)
            ItemInstance.objects.filter(pk=mine.pk).update(
                durability_current=50.0)
            make_vendor('pn', room, [(sword, 12)])
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_examine('iron sword')
        msgs = outputs(sent)
        # The carried instance (50%) resolves, not the vendor entry.
        self.assertIn('Durability: 50%', msgs[0]['text'])


class UseSequenceTests(TransactionTestCase):
    """#61/#65 and DD §7: heal sequences."""

    def _setup(self, prefix, draughts=3, vitality=(10, 100)):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        current, maximum = vitality
        Character.objects.filter(pk=char.pk).update(
            vitality_current=current, vitality_max=maximum)
        char.vitality_current, char.vitality_max = current, maximum
        heal = EffectDefinition.objects.create(
            name=f'{prefix} Heal', slug=f'{prefix}-heal')
        EffectComponent.objects.create(
            definition=heal, component_type='restore_vitality',
            magnitude_base=60.0, magnitude_scaling=0.0,
            duration_base=0.0, duration_scaling=0.0,
        )
        draught_def = make_item_def(prefix, 'Healing Draught', 'consumable',
                                    effect=heal)
        for _ in range(draughts):
            make_owned_item(draught_def, char)
        return char

    async def test_sequence_stops_at_full_with_the_loot_line(self):
        char = await sync_to_async(self._setup)('usA')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('3 healing draught')
        texts = [m['text'] for m in outputs(sent)]
        use_lines = [t for t in texts if t.startswith('You use a Healing Draught')]
        # 10 → 70 → full at the second draught; the third never fires.
        self.assertEqual(len(use_lines), 2)
        full = [m for m in outputs(sent)
                if m['text'] == 'You have been restored to full health.']
        self.assertEqual(len(full), 1)
        self.assertEqual(full[0]['category'], 'reward')

        def remaining():
            return ItemInstance.objects.filter(owner=char).count()
        self.assertEqual(await sync_to_async(remaining)(), 1)

    async def test_heal_at_full_refused_warn(self):
        char = await asyncio.to_thread(
            self._setup, 'usB', vitality=(100, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(msgs[0]['text'], 'You are already at full health.')

        def remaining():
            return ItemInstance.objects.filter(owner=char).count()
        self.assertEqual(await sync_to_async(remaining)(), 3)


class SpendTests(TransactionTestCase):
    """DD §1: the spend order flip (footnotes 7/14/15)."""

    def _char(self, prefix, points=5):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        Character.objects.filter(pk=char.pk).update(unspent_stat_points=points)
        return char

    async def test_new_order_spends_and_sentences(self):
        char = await sync_to_async(self._char)('spA')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('2 dex')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('You spend 2 points on Dexterity.', texts)

        def dex():
            return Character.objects.get(pk=char.pk).stat_dex
        self.assertEqual(await sync_to_async(dex)(), 12)

    async def test_old_order_errors(self):
        char = await sync_to_async(self._char)('spB')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('dex 2')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'error')
        self.assertIn('Usage: spend', msgs[0]['text'])

    async def test_bare_numeric_names_the_missing_stat(self):
        char = await sync_to_async(self._char)('spC')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('3')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'error')
        self.assertEqual(msgs[0]['text'], 'spend 3 points on which stat?')

    async def test_spend_all(self):
        char = await sync_to_async(self._char)('spD')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('all str')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('You spend 5 points on Strength.', texts)


class SettingsTests(TransactionTestCase):
    """DD §10: six words, sentences, defaults, persistence."""

    async def test_six_words_any_case_and_sentences(self):
        zone, room = await sync_to_async(make_world)('stA')
        char = await sync_to_async(make_character)('stA', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_brief('YES')
        self.assertEqual(outputs(sent)[-1]['text'],
                         'brief room display is now on.')
        await consumer.cmd_brief('false')
        self.assertEqual(outputs(sent)[-1]['text'],
                         'brief room display is now off.')
        await consumer.cmd_brief('')
        self.assertEqual(outputs(sent)[-1]['text'],
                         'brief room display is off.')

    async def test_seventh_word_is_a_usage_error(self):
        zone, room = await sync_to_async(make_world)('stB')
        char = await sync_to_async(make_character)('stB', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_brief('maybe')
        msg = outputs(sent)[-1]
        self.assertEqual(msg['category'], 'error')
        self.assertEqual(msg['text'], 'Usage: brief [on|off]')

    async def test_echo_persists_and_sentences(self):
        zone, room = await sync_to_async(make_world)('stC')
        char = await sync_to_async(make_character)('stC', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_echo('off')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('command echo is now off.', texts)

        def echo_mode():
            return Character.objects.get(pk=char.pk).echo_mode
        self.assertFalse(await sync_to_async(echo_mode)())

    async def test_timestamps_sentences(self):
        zone, room = await sync_to_async(make_world)('stD')
        char = await sync_to_async(make_character)('stD', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_timestamps('no')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('output timestamps are now off.', texts)

    def test_defaults_brief_off_echo_on_timestamps_on(self):
        field = {f.name: f for f in Character._meta.get_fields()
                 if hasattr(f, 'default')}
        self.assertFalse(field['brief_mode'].default)
        self.assertTrue(field['echo_mode'].default)
        self.assertTrue(field['show_timestamps'].default)


class SayTests(TransactionTestCase):
    """DD §13: 'Name: message' in say-color, both speakers, no prefix."""

    async def test_player_say_format_and_category(self):
        zone, room = await sync_to_async(make_world)('sayA')
        char = await sync_to_async(make_character)('sayA', room)
        sent = []
        consumer = make_stub_consumer(char, sent)

        async def no_dialogue(text):
            pass
        consumer.schedule_npc_dialogue_responses = no_dialogue

        await consumer.cmd_say('hello there')
        self.assertEqual(len(consumer.channel_layer.events), 1)
        group, event = consumer.channel_layer.events[0]
        self.assertEqual(event['category'], 'say')
        self.assertEqual(event['text'], 'sayA Char: hello there')
        self.assertNotIn('[say]', event['text'])

    async def test_npc_response_format_and_category(self):
        zone, room = await sync_to_async(make_world)('sayB')

        def setup():
            char = make_character('sayB', room)
            definition = NpcDefinition.objects.create(
                name='Aldric the Greeter', slug='sayb-aldric',
                description='x', genre_tag='fantasy', article='',
                base_vitality=10, base_str=1, base_dex=1, base_end=1,
                base_int=1, base_wis=1, base_per=1,
            )
            npc = NpcInstance.objects.create(
                definition=definition, current_room=room, spawn_room=room,
                vitality_current=10, vitality_max=10,
            )
            entry = DialogueEntry.objects.create(
                npc_definition=definition, entry_type='keyword',
                keywords=['hello'],
            )
            DialogueResponse.objects.create(entry=entry, text='Well met.')
            row = PendingDialogueResponse.objects.create(
                utterance_id=uuid.uuid4(), npc_instance=npc, entry=entry,
                character=char, room=room, position=0, is_final=False,
                fire_at=timezone.now(),
            )
            return PendingDialogueResponse.objects.select_related(
                'npc_instance__definition').get(pk=row.pk)
        row = await sync_to_async(setup)()

        from apps.shyland.management.commands.run_tick_engine import Command
        cmd = Command()
        broadcasts = []

        async def record(room_id, text, category='room', exclude_pk=None,
                         exclude_pks=None):
            broadcasts.append((room_id, text, category))
        cmd.broadcast_to_room = record

        await cmd.deliver_dialogue_response(row)
        say_lines = [b for b in broadcasts if b[2] == 'say']
        self.assertEqual(len(say_lines), 1)
        self.assertEqual(say_lines[0][1], 'Aldric the Greeter: Well met.')
        self.assertNotIn('[say]', say_lines[0][1])


class CritProseTests(TransactionTestCase):
    """DD §13 / #54: no '[Critical]' bracket anywhere; the word moves into
    the damage clause; NPC crits emit combat-crit-in."""

    async def test_forced_crit_round(self):
        def setup():
            zone, room = make_world('crit')
            char = make_character('crit', room)
            Character.objects.filter(pk=char.pk).update(
                vitality_current=500, vitality_max=500)
            definition = NpcDefinition.objects.create(
                name='crit beetle', slug='crit-beetle',
                description='x', genre_tag='fantasy',
                base_vitality=1000, base_str=1, base_dex=1, base_end=1,
                base_int=1, base_wis=1, base_per=1,
            )
            npc = NpcInstance.objects.create(
                definition=definition, current_room=room, spawn_room=room,
                vitality_current=1000, vitality_max=1000,
            )
            from apps.shyland.models import COMBAT_ROUND_TICKS
            session = CombatSession.objects.create(
                room=room, last_tick_at=timezone.now(),
                tick_counter=COMBAT_ROUND_TICKS - 1,
            )
            session.characters.add(char)
            session.npcs.add(npc)
            return char
        char = await sync_to_async(setup)()

        from apps.shyland.management.commands.run_tick_engine import Command
        cmd = Command()
        player_msgs = []
        room_msgs = []

        async def record_send(character_pk, text, category, status,
                              event=None, fight=None):
            if text:
                player_msgs.append((character_pk, text, category))

        async def record_broadcast(room_id, text, category='room',
                                   exclude_pk=None, exclude_pks=None):
            room_msgs.append((room_id, text, category))
        cmd.send_to_player = record_send
        cmd.broadcast_to_room = record_broadcast

        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='critical'):
            await cmd.process_combat(1)

        all_texts = [t for _, t, _ in player_msgs] + [t for _, t, _ in room_msgs]
        self.assertTrue(all_texts)
        for text in all_texts:
            self.assertNotIn('[Critical]', text)

        out_crits = [m for m in player_msgs if m[2] == 'combat-crit-out']
        self.assertTrue(out_crits)
        # Unarmed player crit: the word lives in the damage clause.
        self.assertRegex(out_crits[0][1], r'for a critical \d+ damage!')

        in_crits = [m for m in player_msgs if m[2] == 'combat-crit-in']
        self.assertTrue(in_crits)
        self.assertRegex(in_crits[0][1], r'for a critical \d+ damage!')


class RepairAllCapTests(TransactionTestCase):
    """#75: repair all retries bounded at 5 passes."""

    async def test_five_pass_cap_on_stubborn_items(self):
        def setup():
            zone, room = make_world('rep')
            char = make_character('rep', room)
            Character.objects.filter(pk=char.pk).update(copper=10_000)
            gear = make_item_def('rep', 'Iron Helm', base_value=10,
                                 takes_durability=True)
            item = make_owned_item(gear, char)
            ItemInstance.objects.filter(pk=item.pk).update(
                durability_current=40.0)
            repairer_def = NpcDefinition.objects.create(
                name='rep Mender', slug='rep-mender',
                description='x', genre_tag='fantasy', is_repairer=True,
                base_vitality=10, base_str=1, base_dex=1, base_end=1,
                base_int=1, base_wis=1, base_per=1,
            )
            NpcInstance.objects.create(
                definition=repairer_def, current_room=room, spawn_room=room,
                vitality_current=10, vitality_max=10,
            )
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        with mock.patch('apps.shyland.consumers.get_repair_success_chance',
                        return_value=0.0):
            await consumer.cmd_repair('all')
        texts = [m['text'] for m in outputs(sent)]
        failed_lines = [t for t in texts if "didn't take" in t]
        self.assertEqual(len(failed_lines), 5)
        self.assertIn('Repaired 0 items, 5 attempts failed', texts[-1])


class NameInvariantTests(TestCase):
    """#122: both enforcement edges."""

    def setUp(self):
        self.zone, self.room = make_world('ni')
        NpcDefinition.objects.create(
            name='Silk Matron', slug='ni-silk-matron',
            description='x', genre_tag='fantasy',
            base_vitality=10, base_str=1, base_dex=1, base_end=1,
            base_int=1, base_wis=1, base_per=1,
        )
        self.origin = Origin.objects.create(
            name='ni Origin', slug='ni-origin',
            acuity_baseline=1.0, acuity_band_low=0.8, acuity_band_high=1.2,
        )
        self.archetype = Archetype.objects.create(
            name='ni Archetype', slug='ni-archetype',
            primary_stat_1='str', primary_stat_2='dex',
        )

    def _form(self, name):
        return CharacterCreationForm(data={
            'origin': self.origin.pk,
            'archetype': self.archetype.pk,
            'name': name,
        })

    def test_creation_rejects_npc_colliding_name_case_insensitively(self):
        for attempt in ('Silk Matron', 'silk matron', 'SILK MATRON'):
            form = self._form(attempt)
            self.assertFalse(form.is_valid(), attempt)
            self.assertIn('That name belongs to the world already.',
                          form.errors['name'])

    def test_creation_accepts_a_clean_name(self):
        form = self._form('Wandering Star')
        self.assertTrue(form.is_valid(), form.errors)

    def test_seed_verify_carries_the_check(self):
        # The authoring edge lives in seed_world._verify; pin its presence
        # and exercise the same case-insensitive comparison it performs.
        import inspect
        from apps.shyland.management.commands import seed_world
        source = inspect.getsource(seed_world)
        self.assertIn(
            'no NPC definition name collides with any existing character name',
            source,
        )
        user = User.objects.create_user(username='ni_user2', password='x')
        Character.objects.create(
            user=user, name='SILK matron',
            origin=self.origin, archetype=self.archetype,
            current_room=self.room, recall_room=self.room,
        )
        npc_names = {n.lower() for n in
                     NpcDefinition.objects.values_list('name', flat=True)}
        char_names = {n.lower() for n in
                      Character.objects.values_list('name', flat=True)}
        self.assertEqual(npc_names & char_names, {'silk matron'})


class LootChartTests(TransactionTestCase):
    """DD §1: loot is 'all | <NPC>' — corpse forms only."""

    async def test_loot_by_npc_name_and_not_your_kill_warn(self):
        def setup():
            zone, room = make_world('lc')
            char = make_character('lc', room)
            other = make_character('lc2', room)
            definition = NpcDefinition.objects.create(
                name='lc boar', slug='lc-boar',
                description='x', genre_tag='fantasy',
                base_vitality=10, base_str=1, base_dex=1, base_end=1,
                base_int=1, base_wis=1, base_per=1,
            )
            Corpse.objects.create(
                npc_definition=definition, npc_name_snapshot='the lc boar',
                current_room=room, killed_by=other, copper_drop=0,
                decay_at=timezone.now() + timedelta(hours=1),
            )
            return char
        char = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_loot('boar')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertIn('not your kill', msgs[0]['text'])
