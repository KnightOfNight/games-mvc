"""v24.4 Brief 1 — the heal command (#166).

Registration (COMMAND_TABLE / DYING_ALLOWED / gating-set absences), the
six output-table cases, the gate order (at-full beats empty-pool), the
oldest-first mixed-Mk consumption (#168) under the Draught Law, combat
passage, the dying single-consume revival, args-ignored dispatch, and
the help row / verb-completion surface.

Output-table row → test map (brief §1):
  1 → AtFullTests (both)         2 → NoDraughtsTests.test_no_qualifying_*
  3 → CoverTests                 4 → ShortfallTests
  5 → DyingTests.test_dying_consumes_one_and_revives
  6 → DyingTests.test_dying_with_no_draughts_warns
"""

import json

from asgiref.sync import sync_to_async

from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import DIRECTIONS, SkylandConsumer
from apps.shyland.models import (
    Character, CombatSession, EffectComponent, EffectDefinition,
    ItemInstance, NpcDefinition, NpcInstance,
)

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world, outputs,
)
from .test_use_output_merge import (
    make_heal_effect, remaining, setup_draughts,
)


class FakeRedis:
    async def keys(self, *args):
        return []

    async def mget(self, *args):
        return []


def statuses(sent):
    return [m for m in sent if m.get('type') == 'status']


class RegistrationTests(SimpleTestCase):
    """Brief §2 step 2: the four registration points and the absences."""

    def test_command_table_entry(self):
        self.assertEqual(SkylandConsumer.COMMAND_TABLE['heal'],
                         ('cmd_heal', False))

    def test_dying_allowed(self):
        self.assertIn('heal', SkylandConsumer.DYING_ALLOWED)

    def test_absent_from_the_other_gating_sets(self):
        self.assertNotIn('heal', SkylandConsumer.COMBAT_BLOCKED)
        self.assertNotIn('heal', SkylandConsumer.PROMPT_VERBS)
        self.assertNotIn('heal', SkylandConsumer.GRAMMAR_VERBS)
        self.assertNotIn('heal', SkylandConsumer.ADMIN_VERBS)

    def test_verb_completion_includes_heal(self):
        # The connect-time verbs payload derives from the dispatch table
        # (v20 brief 3, #19) — heal flows into completion from there.
        self.assertIn('heal', set(DIRECTIONS) | set(SkylandConsumer.COMMAND_TABLE))

    def test_help_row_between_flee_and_home(self):
        action_rows = dict(SkylandConsumer.HELP_SECTIONS)['Action commands']
        row = ('heal', 'heal',
               'Drink healing draughts until your vitality is full.')
        self.assertIn(row, action_rows)
        commands = [r[0] for r in action_rows]
        self.assertLess(commands.index('flee'), commands.index('heal'))
        self.assertLess(commands.index('heal'), commands.index('home'))


class AtFullTests(TransactionTestCase):
    """Output table case 1: the #61 refusal, with and without draughts —
    the gate order (at-full beats empty-pool)."""

    async def test_at_full_with_draughts_refuses(self):
        char, _ = await sync_to_async(setup_draughts)(
            'hfA', count=3, vitality=(100, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'You are already at full health.')
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(await sync_to_async(remaining)(char), 3)
        self.assertEqual(statuses(sent), [])

    async def test_at_full_with_no_draughts_still_refuses(self):
        # Gate order: heal's purpose is already fulfilled — the at-full
        # refusal fires, never the empty-pool warn.
        char, _ = await sync_to_async(setup_draughts)(
            'hfB', count=0, vitality=(100, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'You are already at full health.')
        self.assertEqual(msgs[0]['category'], 'warn')


class NoDraughtsTests(TransactionTestCase):
    """Output table case 2: damaged with no qualifying draughts."""

    async def test_no_qualifying_draughts_warns(self):
        char, _ = await sync_to_async(setup_draughts)(
            'ndA', count=0, vitality=(10, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], 'You have no healing draughts.')
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(statuses(sent), [])

    async def test_no_qualifying_draughts_is_mechanical_not_a_name_match(self):
        # A carried consumable whose effect is timed does not qualify,
        # whatever it is called (§1.4).
        def setup():
            char, _ = setup_draughts('ndB', count=0, vitality=(10, 100))
            tonic_effect = EffectDefinition.objects.create(
                name='ndB Focus', slug='ndb-focus')
            EffectComponent.objects.create(
                definition=tonic_effect, component_type='shift_acuity_high',
                magnitude_base=0.3, magnitude_scaling=0.0,
                duration_base=60.0, duration_scaling=0.0,
            )
            tonic_def = make_item_def('ndB', 'Healing Draught Tonic',
                                      'consumable', effect=tonic_effect)
            make_owned_item(tonic_def, char)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], 'You have no healing draughts.')
        self.assertEqual(await sync_to_async(remaining)(char), 1)


class QualifyingPoolTests(TransactionTestCase):
    """§1.4: qualification is the per-item aggregate test — an instant
    restorative qualifies whatever its name (never a name match)."""

    async def test_non_draught_named_restorative_qualifies(self):
        def setup():
            zone, room = make_world('qpA')
            char = make_character('qpA', room)
            Character.objects.filter(pk=char.pk).update(
                vitality_current=75, vitality_max=100)
            heal = make_heal_effect('qpA', magnitude=25.0)
            elixir_def = make_item_def('qpA', 'Vital Elixir', 'consumable',
                                       effect=heal)
            make_owned_item(elixir_def, char)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Vital Elixir Mk 1 and feel your body recover. '
            '(+25 Vitality) You are restored to full health.')
        self.assertEqual(msgs[0]['category'], 'reward')
        self.assertEqual(await sync_to_async(remaining)(char), 0)


class CoverTests(TransactionTestCase):
    """Output table case 3: minimum count consumed, surplus untouched,
    one reward line with the full-heal fold, one status payload."""

    async def test_exact_cover_consumes_the_minimum(self):
        # Deficit 45 at 25/heal needs 2 of the 3 carried.
        char, _ = await sync_to_async(setup_draughts)(
            'cvA', count=3, magnitude=25.0, vitality=(55, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use Healing Draught Mk 1 ×2 and feel your body recover. '
            '(+50 Vitality) You are restored to full health.')
        self.assertEqual(msgs[0]['category'], 'reward')
        self.assertEqual(await sync_to_async(remaining)(char), 1)
        self.assertEqual(len(statuses(sent)), 1)

        def vitality():
            return Character.objects.get(pk=char.pk).vitality_current
        self.assertEqual(await sync_to_async(vitality)(), 100)


class ShortfallTests(TransactionTestCase):
    """Output table case 4: supply exhausted short of full — success
    line, then the standing shortfall warn (#132) on its own line."""

    async def test_shortfall_consumes_all_and_warns(self):
        char, _ = await sync_to_async(setup_draughts)(
            'sfA', count=2, magnitude=25.0, vitality=(10, 1000))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(
            msgs[0]['text'],
            'You use Healing Draught Mk 1 ×2 and feel your body recover. '
            '(+50 Vitality)')
        self.assertEqual(msgs[0]['category'], 'success')
        self.assertEqual(msgs[1]['text'], 'You only had 2.')
        self.assertEqual(msgs[1]['category'], 'warn')
        self.assertEqual(await sync_to_async(remaining)(char), 0)
        self.assertEqual(len(statuses(sent)), 1)


class OldestFirstTests(TransactionTestCase):
    """§1.3 (#168): oldest-first regardless of Mk; each item heals from
    its own Mk under the Draught Law; comma-joined mixed-Mk sentence."""

    async def test_oldest_first_mixed_mk_consumption(self):
        def setup():
            zone, room = make_world('ofA')
            char = make_character('ofA', room)
            Character.objects.filter(pk=char.pk).update(
                vitality_current=10, vitality_max=1000)
            heal = make_heal_effect('ofA', magnitude=25.0, scaling=5.0)
            draught_def = make_item_def('ofA', 'Healing Draught',
                                        'consumable', effect=heal)
            # Older Mk 1 first, newer Mk 2 second.
            ItemInstance.objects.create(
                definition=draught_def, owner=char, mk_tier=1,
                rarity='common', durability_current=100.0,
                is_identified=True)
            ItemInstance.objects.create(
                definition=draught_def, owner=char, mk_tier=2,
                rarity='common', durability_current=100.0,
                is_identified=True)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_heal()
        msgs = outputs(sent)
        # Mk 1 heals 30, Mk 2 heals 35 — consumption order is age, the
        # per-item heal is each item's own Mk.
        self.assertEqual(
            msgs[0]['text'],
            'You use Healing Draught Mk 1 ×1, Healing Draught Mk 2 ×1 '
            'and feel your body recover. (+65 Vitality)')
        self.assertEqual(await sync_to_async(remaining)(char), 0)


class CombatTests(TransactionTestCase):
    """§1.5 / output table row 7 of the playtest list: heal proceeds in
    combat exactly as use does — no state refusal."""

    def _combat(self, char, room, prefix):
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

    async def test_heal_proceeds_in_combat(self):
        char, _ = await sync_to_async(setup_draughts)(
            'cbA', count=3, magnitude=25.0, vitality=(55, 100))

        def combat():
            self._combat(char, char.current_room, 'cbA')
        await sync_to_async(combat)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('heal', '')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertTrue(
            msgs[0]['text'].endswith('You are restored to full health.'),
            msgs[0]['text'])
        self.assertEqual(msgs[0]['category'], 'reward')
        self.assertEqual(await sync_to_async(remaining)(char), 1)


class DyingTests(TransactionTestCase):
    """Output table cases 5 and 6: the dying single-consume revival and
    the dying empty-pool warn; the dying gate passes heal."""

    async def test_dying_consumes_one_and_revives(self):
        def setup():
            char, _ = setup_draughts('dgA', count=3, magnitude=25.0,
                                     vitality=(0, 100))
            Character.objects.filter(pk=char.pk).update(is_dying=True)
            char.is_dying = True
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer.redis = FakeRedis()
        await consumer.cmd_heal()
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

    async def test_dying_with_no_draughts_warns(self):
        # Through receive_json — proves the dying gate passes heal to
        # the handler (no "You are dying!" refusal) and case 6 renders.
        def setup():
            char, _ = setup_draughts('dgB', count=0, vitality=(0, 100))
            Character.objects.filter(pk=char.pk).update(is_dying=True)
            char.is_dying = True
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.receive_json({'text': 'heal'})
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['category'], 'echo')
        self.assertEqual(msgs[1]['text'], 'You have no healing draughts.')
        self.assertEqual(msgs[1]['category'], 'warn')


class ArgsIgnoredTests(TransactionTestCase):
    """§1.1 (DD §9.1 fn 2): all arguments ignored — `heal 5 draughts`
    behaves exactly as bare `heal`."""

    async def test_arguments_are_ignored(self):
        char, _ = await sync_to_async(setup_draughts)(
            'aiA', count=3, magnitude=25.0, vitality=(55, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('heal', '5 draughts')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use Healing Draught Mk 1 ×2 and feel your body recover. '
            '(+50 Vitality) You are restored to full health.')
        self.assertEqual(await sync_to_async(remaining)(char), 1)


class HelpTests(TransactionTestCase):
    """Brief step 4: the heal row renders for a regular player."""

    async def test_help_renders_the_heal_row(self):
        def setup():
            zone, room = make_world('hpA')
            return make_character('hpA', room)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_help()
        blob = json.dumps(sent)
        self.assertIn('Drink healing draughts until your vitality is full.',
                      blob)
