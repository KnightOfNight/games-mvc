"""v24.5 Brief 1 — bare loot behaves like loot all (#189).

The dispatch-table change (loot out of PROMPT_VERBS; GRAMMAR_VERBS and
COMBAT_BLOCKED untouched), bare ≡ all verbatim on the sweep path, the
kill-gate refusal, the empty-room warn, the unchanged single-corpse and
explicit-all forms, the in-combat refusal for the bare form, and the
help row. Loot is the first and only bare-sweep verb — deliberately NOT
a precedent for sell (#150).
"""

from asgiref.sync import sync_to_async
from datetime import timedelta

from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    CombatSession, Corpse, ItemInstance, NpcDefinition, NpcInstance,
)

from .test_command_revamp import (
    make_character, make_item_def, make_stub_consumer, make_world, outputs,
)


def make_npc_def(prefix, name):
    return NpcDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        description='x', genre_tag='fantasy',
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )


def make_corpse(defn, room, killed_by, copper_drop=0):
    return Corpse.objects.create(
        npc_definition=defn, npc_name_snapshot=f'the {defn.name}',
        current_room=room, killed_by=killed_by, copper_drop=copper_drop,
        decay_at=timezone.now() + timedelta(hours=1),
    )


def sweep_fixtures(prefix):
    """Two corpses killed by the character: one carrying coin and an
    item, one empty-handed — the sweep emits loot lines plus the
    'carried nothing' summary. Returns (char, rebuild) where rebuild()
    recreates the identical corpse set (same definitions, same drops,
    same creation order) after a sweep has consumed the first."""
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    boar = make_npc_def(prefix, f'{prefix} boar')
    wisp = make_npc_def(prefix, f'{prefix} wisp')
    fang = make_item_def(prefix, f'{prefix} Fang')

    def build():
        corpse = make_corpse(boar, room, char, copper_drop=25)
        ItemInstance.objects.create(
            definition=fang, corpse=corpse, mk_tier=1, rarity='common',
            durability_current=100.0, is_identified=True,
        )
        make_corpse(wisp, room, char, copper_drop=0)

    build()
    return char, build


def texts_and_categories(sent):
    return [(m['text'], m['category']) for m in outputs(sent)]


class TableTests(SimpleTestCase):
    """Brief §5.1: the dispatch-table deltas and non-deltas."""

    def test_loot_left_prompt_verbs(self):
        self.assertNotIn('loot', SkylandConsumer.PROMPT_VERBS)

    def test_loot_still_in_grammar_verbs(self):
        self.assertEqual(SkylandConsumer.GRAMMAR_VERBS.get('loot'), 'loot')

    def test_loot_still_combat_blocked_with_the_authored_line(self):
        self.assertEqual(SkylandConsumer.COMBAT_BLOCKED['loot'],
                         'Your hands are too busy with the fight!')

    def test_no_other_verb_left_prompt_verbs(self):
        # Footnote 10 untouched for every other command: the v22 set
        # minus exactly loot.
        self.assertEqual(SkylandConsumer.PROMPT_VERBS, {
            'attack': 'attack', 'kill': 'attack', 'k': 'attack',
            'buy': 'buy',
            'drop': 'drop',
            'equip': 'equip', 'eq': 'equip',
            'examine': 'examine', 'ex': 'examine',
            'pickup': 'pickup', 'p': 'pickup',
            'repair': 'repair',
            'say': 'say',
            'sell': 'sell',
            'spend': 'spend',
            'unequip': 'unequip', 'uneq': 'unequip',
            'use': 'use',
        })

    def test_help_row(self):
        action_rows = dict(SkylandConsumer.HELP_SECTIONS)['Action commands']
        self.assertIn(
            ('loot', 'loot [all] | <NPC>',
             'Loot every corpse here, or one named corpse.'),
            action_rows,
        )


class BareEqualsAllTests(TransactionTestCase):
    """Brief §5.2–4: bare loot ≡ loot all, verbatim, in every case."""

    async def test_bare_sweep_output_identical_to_all(self):
        char, rebuild = await sync_to_async(sweep_fixtures)('blA')

        bare_sent = []
        consumer = make_stub_consumer(char, bare_sent)
        await consumer._dispatch('loot', '')
        bare = texts_and_categories(bare_sent)

        # The sweep emptied and disposed the corpses; recreate the
        # identical set and run the explicit form.
        await sync_to_async(rebuild)()
        all_sent = []
        consumer = make_stub_consumer(char, all_sent)
        await consumer._dispatch('loot', 'all')
        self.assertEqual(bare, texts_and_categories(all_sent))

        # The sweep actually ran: loot lines plus the summary counting
        # the empty-handed corpse.
        self.assertEqual(bare[-1],
                         ('Looted 2 corpses; 1 carried nothing worth taking.',
                          'system'))
        self.assertTrue(any(t.startswith('You loot ') for t, _ in bare), bare)
        # The fn-10 prompt is unreachable for loot.
        self.assertNotIn('What do you want to loot?', [t for t, _ in bare])

    async def test_bare_kill_gate_refusal(self):
        def setup():
            zone, room = make_world('blB')
            char = make_character('blB', room)
            other = make_character('blB2', room)
            make_corpse(make_npc_def('blB', 'blB boar'), room, other)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('loot', '')
        self.assertEqual(texts_and_categories(sent),
                         [('That is not your kill; you may not loot it.',
                           'warn')])

    async def test_bare_empty_room(self):
        def setup():
            zone, room = make_world('blC')
            return make_character('blC', room)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('loot', '')
        self.assertEqual(texts_and_categories(sent),
                         [('There is nothing to loot here.', 'warn')])


class UnchangedFormsTests(TransactionTestCase):
    """Brief §5.5: the explicit forms ride the same fixtures unchanged."""

    async def test_loot_all_still_sweeps(self):
        char, _ = await sync_to_async(sweep_fixtures)('ufA')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('loot', 'all')
        lines = texts_and_categories(sent)
        self.assertEqual(lines[-1],
                         ('Looted 2 corpses; 1 carried nothing worth taking.',
                          'system'))

    async def test_loot_by_npc_name_still_single_corpse(self):
        char, _ = await sync_to_async(sweep_fixtures)('ufB')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('loot', 'boar')
        lines = texts_and_categories(sent)
        # The named corpse only: its coin and item lines, no sweep
        # summary, the wisp corpse untouched.
        self.assertTrue(all(c == 'reward' for _, c in lines), lines)
        self.assertTrue(any('ufB Fang' in t for t, _ in lines), lines)
        self.assertFalse(any(t.startswith('Looted ') for t, _ in lines))

        def wisp_corpse_count():
            return Corpse.objects.filter(
                npc_name_snapshot__contains='wisp').count()
        self.assertEqual(await sync_to_async(wisp_corpse_count)(), 1)


class CombatTests(TransactionTestCase):
    """Bare loot in combat hits the authored COMBAT_BLOCKED refusal,
    exactly as loot all does."""

    async def test_bare_loot_refused_in_combat(self):
        def setup():
            char, _rebuild = sweep_fixtures('cbL')
            defn = make_npc_def('cbL', 'cbL snarler')
            npc = NpcInstance.objects.create(
                definition=defn, current_room=char.current_room,
                spawn_room=char.current_room,
                vitality_current=10, vitality_max=10,
            )
            session = CombatSession.objects.create(
                room=char.current_room, last_tick_at=timezone.now(),
            )
            session.characters.add(char)
            session.npcs.add(npc)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('loot', '')
        self.assertEqual(texts_and_categories(sent),
                         [('Your hands are too busy with the fight!',
                           'warn')])
