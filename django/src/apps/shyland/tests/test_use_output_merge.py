"""v23.3 Brief 1 — Use Output Merge (#149/#151).

The effect layer's clause contract, the merged use sentence, the
instant-restore aggregate path (deficit math, single vitality write,
Amendment-5 count-form line, full-heal fold, shortfall warn), the
unchanged #61 gate and dying/revival semantics, and the NPC path's
byte-identical recomposition.
"""

from asgiref.sync import sync_to_async

from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext

from apps.shyland.combat_utils import apply_npc_effects
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.effect_utils import (
    compose_standalone_sentence, compose_use_sentence,
)
from apps.shyland.models import (
    Character, EffectComponent, EffectDefinition, ItemInstance,
    NpcDefinition, NpcEffect, NpcInstance,
)

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world, outputs,
)


def make_heal_effect(prefix, magnitude=25.0, scaling=0.0):
    heal = EffectDefinition.objects.create(
        name=f'{prefix} Heal', slug=f'{prefix}-heal')
    EffectComponent.objects.create(
        definition=heal, component_type='restore_vitality',
        magnitude_base=magnitude, magnitude_scaling=scaling,
        duration_base=0.0, duration_scaling=0.0,
    )
    return heal


def setup_draughts(prefix, count=3, magnitude=25.0, scaling=0.0,
                   vitality=(10, 100)):
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    current, maximum = vitality
    Character.objects.filter(pk=char.pk).update(
        vitality_current=current, vitality_max=maximum)
    char.vitality_current, char.vitality_max = current, maximum
    heal = make_heal_effect(prefix, magnitude, scaling)
    draught_def = make_item_def(prefix, 'Healing Draught', 'consumable',
                                effect=heal)
    for _ in range(count):
        make_owned_item(draught_def, char)
    return char, draught_def


def remaining(char):
    return ItemInstance.objects.filter(owner=char).count()


class MergedSingleUseTests(TransactionTestCase):
    """§4.1/§4.2: the merged single-use line; timed effects stay plain."""

    async def test_merged_single_use_line_exact(self):
        char, _ = await sync_to_async(setup_draughts)('umA', count=1)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        # One output envelope; no separate system-category effect line.
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Healing Draught Mk 1 and feel your body recover. '
            '(+25 Vitality)')
        self.assertEqual(msgs[0]['category'], 'success')
        self.assertFalse([m for m in msgs if m['category'] == 'system'])

    async def test_timed_effect_stays_the_plain_sentence(self):
        def setup():
            zone, room = make_world('umB')
            char = make_character('umB', room)
            tonic_effect = EffectDefinition.objects.create(
                name='umB Focus', slug='umb-focus')
            EffectComponent.objects.create(
                definition=tonic_effect, component_type='shift_acuity_high',
                magnitude_base=0.3, magnitude_scaling=0.0,
                duration_base=60.0, duration_scaling=0.0,
            )
            tonic_def = make_item_def('umB', 'Focus Tonic', 'consumable',
                                      effect=tonic_effect)
            make_owned_item(tonic_def, char)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('focus tonic')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'You use a Focus Tonic Mk 1.')
        self.assertEqual(msgs[0]['category'], 'success')


class AggregateMathTests(TransactionTestCase):
    """§4.3: deficit-driven stop, N-cap, inventory-cap, resolver order."""

    async def test_deficit_driven_stop_consumes_the_needed_count(self):
        # Deficit 90 at 60/heal needs 2, not the 5 asked for.
        char, _ = await sync_to_async(setup_draughts)(
            'agA', count=5, magnitude=60.0, vitality=(10, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('5 healing draught')
        self.assertEqual(await sync_to_async(remaining)(char), 3)
        texts = [m['text'] for m in outputs(sent)]
        self.assertTrue(any('×2' in t for t in texts), texts)

    async def test_request_cap_consumes_the_asked_count(self):
        # Deficit 490 far exceeds two draughts — the ask caps the run.
        char, _ = await sync_to_async(setup_draughts)(
            'agB', count=5, magnitude=60.0, vitality=(10, 500))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('2 healing draught')
        self.assertEqual(await sync_to_async(remaining)(char), 3)
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use Healing Draught Mk 1 ×2 and feel your body recover. '
            '(+120 Vitality)')
        self.assertEqual(msgs[0]['category'], 'success')

    async def test_inventory_cap_consumes_everything(self):
        char, _ = await sync_to_async(setup_draughts)(
            'agC', count=2, magnitude=60.0, vitality=(10, 1000))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('5 healing draught')
        self.assertEqual(await sync_to_async(remaining)(char), 0)

    async def test_resolver_order_is_preserved_not_resorted(self):
        # A common Mk 2 outranks an uncommon Mk 1 in the resolver's
        # lowest-value-first order; the line must keep that order, not
        # re-sort by tier.
        def setup():
            zone, room = make_world('agD')
            char = make_character('agD', room)
            Character.objects.filter(pk=char.pk).update(
                vitality_current=10, vitality_max=1000)
            heal = make_heal_effect('agD', magnitude=25.0, scaling=5.0)
            draught_def = make_item_def('agD', 'Healing Draught',
                                        'consumable', effect=heal)
            ItemInstance.objects.create(
                definition=draught_def, owner=char, mk_tier=1,
                rarity='uncommon', durability_current=100.0,
                is_identified=True)
            ItemInstance.objects.create(
                definition=draught_def, owner=char, mk_tier=2,
                rarity='common', durability_current=100.0,
                is_identified=True)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('2 healing draught')
        msgs = outputs(sent)
        # Mk1 heals 30, Mk2 heals 35; common Mk2 consumes first.
        self.assertEqual(
            msgs[0]['text'],
            'You use Healing Draught Mk 2 ×1, Healing Draught Mk 1 ×1 '
            'and feel your body recover. (+65 Vitality)')


class AggregateLineTests(TransactionTestCase):
    """§4.4: count form, mixed-Mk groups, the count-of-1 article form."""

    async def test_count_of_one_keeps_the_article_form(self):
        # Deficit 30 at 60/heal: one draught covers it — article form,
        # never ×1, even though 3 were asked for.
        char, _ = await sync_to_async(setup_draughts)(
            'alA', count=3, magnitude=60.0, vitality=(70, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('3 healing draught')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Healing Draught Mk 1 and feel your body recover. '
            '(+60 Vitality) You are restored to full health.')
        self.assertEqual(msgs[0]['category'], 'reward')
        self.assertEqual(await sync_to_async(remaining)(char), 2)


class FullHealFoldTests(TransactionTestCase):
    """§4.5: the fold ends the line, reward category, no second message."""

    async def test_fold_is_one_reward_line(self):
        char, _ = await sync_to_async(setup_draughts)(
            'fhA', count=3, magnitude=60.0, vitality=(10, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('3 healing draught')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertTrue(
            msgs[0]['text'].endswith('You are restored to full health.'))
        self.assertEqual(msgs[0]['category'], 'reward')
        # The old separate full-health line never appears.
        self.assertFalse([m for m in msgs
                          if m['text'] == 'You have been restored to full health.'])


class AggregateShortfallTests(TransactionTestCase):
    """§4.6: the warn fires only on request > inventory AND uncovered."""

    async def test_warn_fires_when_uncovered(self):
        char, _ = await sync_to_async(setup_draughts)(
            'asA', count=2, magnitude=60.0, vitality=(10, 1000))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('5 healing draught')
        msgs = outputs(sent)
        warn = [m for m in msgs if m['text'] == 'You only had 2.']
        self.assertEqual(len(warn), 1)
        self.assertEqual(warn[0]['category'], 'warn')

    async def test_no_warn_when_the_stop_was_deficit_driven(self):
        # Request exceeded inventory, but the deficit was covered first.
        char, _ = await sync_to_async(setup_draughts)(
            'asB', count=2, magnitude=60.0, vitality=(10, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('5 healing draught')
        texts = [m['text'] for m in outputs(sent)]
        self.assertFalse([t for t in texts if t.startswith('You only had')],
                         texts)

    async def test_no_warn_when_the_request_was_met(self):
        char, _ = await sync_to_async(setup_draughts)(
            'asC', count=5, magnitude=60.0, vitality=(10, 500))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('2 healing draught')
        texts = [m['text'] for m in outputs(sent)]
        self.assertFalse([t for t in texts if t.startswith('You only had')],
                         texts)


class SingleWriteTests(TestCase):
    """§4.7: exactly one vitality UPDATE; exactly one status payload."""

    def test_aggregate_path_writes_vitality_exactly_once(self):
        char, _ = setup_draughts('swA', count=3, magnitude=25.0,
                                 vitality=(10, 1000))
        items = list(
            ItemInstance.objects.filter(owner=char)
            .select_related('definition', 'definition__effect'))
        apply_aggregate = \
            SkylandConsumer.__dict__['_apply_aggregate_heal'].func
        with CaptureQueriesContext(connection) as ctx:
            consumed, total, covered, extra = apply_aggregate(
                None, char, items, 990)
        vitality_updates = [
            q for q in ctx.captured_queries
            if q['sql'].strip().upper().startswith('UPDATE')
            and 'vitality_current' in q['sql']]
        self.assertEqual(len(vitality_updates), 1)
        self.assertEqual(len(consumed), 3)
        self.assertEqual(total, 75.0)
        self.assertFalse(covered)
        self.assertEqual(extra, [])
        char.refresh_from_db()
        self.assertEqual(char.vitality_current, 85)


class SingleStatusPayloadTests(TransactionTestCase):

    async def test_aggregate_path_sends_one_status_payload(self):
        char, _ = await sync_to_async(setup_draughts)(
            'spA', count=3, magnitude=60.0, vitality=(10, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('3 healing draught')
        statuses = [m for m in sent if m.get('type') == 'status']
        self.assertEqual(len(statuses), 1)


class EntryGateTests(TransactionTestCase):
    """§4.8: the #61 gate is unchanged in wording, category, and effect."""

    async def test_full_health_refusal_unchanged(self):
        char, _ = await sync_to_async(setup_draughts)(
            'egA', count=3, vitality=(100, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], 'You are already at full health.')
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(await sync_to_async(remaining)(char), 3)


class DyingPathTests(TransactionTestCase):
    """§4.9: one restorative consumed, revival intact, merged swallow line."""

    async def test_dying_use_consumes_one_and_revives(self):
        def setup():
            char, _ = setup_draughts('dyA', count=3, magnitude=25.0,
                                     vitality=(0, 100))
            Character.objects.filter(pk=char.pk).update(is_dying=True)
            char.is_dying = True
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)

        class FakeRedis:
            async def keys(self, *args):
                return []

            async def mget(self, *args):
                return []
        consumer.redis = FakeRedis()

        await consumer.cmd_use('healing draught')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn(
            'You use a Healing Draught Mk 1 and feel your body recover. '
            '(+25 Vitality)', texts)
        self.assertIn(
            'Breath floods back into your lungs. You are alive — barely.',
            texts)
        # Exactly one draught swallowed regardless of stack size.
        self.assertEqual(await sync_to_async(remaining)(char), 2)

        def dying():
            return Character.objects.get(pk=char.pk).is_dying
        self.assertFalse(await sync_to_async(dying)())


class NpcPathPinTests(TestCase):
    """§4.10: apply_npc_effects strings byte-identical to the pre-change
    sentences for the representative instant component."""

    def test_npc_instant_restore_sentence_pinned(self):
        zone, room = make_world('npA')
        char = make_character('npA', room)
        Character.objects.filter(pk=char.pk).update(
            vitality_current=10, vitality_max=100)
        heal = make_heal_effect('npA', magnitude=25.0)
        definition = NpcDefinition.objects.create(
            name='npA Lurker', slug='npa-lurker',
            description='A test NPC.', genre_tag='fantasy',
            base_vitality=10, base_str=1, base_dex=1, base_end=1,
            base_int=1, base_wis=1, base_per=1,
        )
        NpcEffect.objects.create(
            npc_definition=definition, effect_definition=heal,
            effect_chance=1.0,
        )
        npc = NpcInstance.objects.create(
            definition=definition, current_room=room, spawn_room=room,
            vitality_current=10, vitality_max=10, mk_tier=1,
        )
        messages = apply_npc_effects(npc, char)
        # The pre-clause-contract sentence, byte for byte, then the
        # effect name the attack line appends.
        self.assertEqual(messages,
                         ['You feel your body recover. (+25 Vitality)',
                          'npA Heal'])


class CompositionHelperTests(TestCase):
    """The two composition forms of the clause contract (§3.1)."""

    def test_standalone_form(self):
        self.assertEqual(
            compose_standalone_sentence(
                ('feel your body recover', '(+25 Vitality)')),
            'You feel your body recover. (+25 Vitality)')
        self.assertEqual(
            compose_standalone_sentence(
                ('watch the repair kit fizz to no useful effect', '')),
            'You watch the repair kit fizz to no useful effect.')

    def test_use_sentence_form(self):
        self.assertEqual(
            compose_use_sentence('a Healing Draught Mk 1',
                                 [('feel your body recover',
                                   '(+25 Vitality)')]),
            'You use a Healing Draught Mk 1 and feel your body recover. '
            '(+25 Vitality)')
        self.assertEqual(
            compose_use_sentence('a Focus Tonic Mk 1', []),
            'You use a Focus Tonic Mk 1.')
        self.assertEqual(
            compose_use_sentence(
                'an Elixir Mk 1',
                [('feel your body recover', '(+25 Vitality)'),
                 ('feel your stamina return', '(+10 Longevity)')]),
            'You use an Elixir Mk 1 and feel your body recover and feel '
            'your stamina return. (+25 Vitality) (+10 Longevity)')
