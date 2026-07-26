"""v23 brief 5 (#40 data half, #144, #147): the authored dialogue corpus
and the speech-vs-narration render rule."""

import inspect

from django.test import SimpleTestCase

from apps.shyland import npc_voice
from apps.shyland.consumers import _tokenize_said_words
from apps.shyland.management.commands.seed_world import (
    DIALOGUE_CONNECTIVES, NPC_DIALOGUE, Command as SeedCommand,
)
from apps.shyland.management.commands.run_tick_engine import (
    Command as TickCommand,
)
from apps.shyland.models import DialogueConnective, DialogueEntry

THE_SIX = ('maro-the-mender', 'essa-the-trader', 'tavik-the-mender',
           'sona-the-trader', 'old-brammel', 'ridda-the-trader')
SILENT = ('the-primordial-sphere', 'the-verdant-sphere',
          'the-verdant-obelisk', 'verdant-shard')


def entries(slug, etype):
    return [s for s in NPC_DIALOGUE[slug] if s['entry_type'] == etype]


class DialogueCorpusTests(SimpleTestCase):

    def test_pool_floor(self):
        for slug, specs in NPC_DIALOGUE.items():
            for s in specs:
                if s['entry_type'] in (DialogueEntry.ENTRY_KEYWORD,
                                       DialogueEntry.ENTRY_DEPARTED):
                    self.assertGreaterEqual(
                        len(s['responses']), 3,
                        f"pool floor: {slug}/{s['entry_type']}:{s['note'] or '-'}")

    def test_greeting_shape(self):
        for slug in NPC_DIALOGUE:
            greets = entries(slug, DialogueEntry.ENTRY_GREETING)
            self.assertEqual(len(greets), 1, slug)
            self.assertEqual(len(greets[0]['responses']), 1, slug)
            self.assertEqual(greets[0]['note'], '', slug)
            self.assertEqual(greets[0]['keywords'], [], slug)

    def test_departure_shape(self):
        for slug in NPC_DIALOGUE:
            deps = entries(slug, DialogueEntry.ENTRY_DEPARTED)
            self.assertEqual(len(deps), 1, slug)
            self.assertEqual(len(deps[0]['responses']), 3, slug)
            self.assertEqual(deps[0]['note'], '', slug)
            self.assertEqual(deps[0]['keywords'], [], slug)

    def test_keyword_entry_shape(self):
        for slug in NPC_DIALOGUE:
            kws = entries(slug, DialogueEntry.ENTRY_KEYWORD)
            self.assertGreaterEqual(len(kws), 2, slug)
            for s in kws:
                self.assertTrue(s['note'], f'{slug}: keyword entry with empty note')
                self.assertGreaterEqual(len(s['keywords']), 1,
                                        f"{slug}:{s['note']}")

    def test_note_uniqueness(self):
        # (entry_type, note) is the seed's reconcile key; a collision
        # would silently merge two pools.
        for slug, specs in NPC_DIALOGUE.items():
            keys = [(s['entry_type'], s['note']) for s in specs]
            self.assertEqual(len(keys), len(set(keys)), slug)

    def test_keyword_token_legality(self):
        for slug, specs in NPC_DIALOGUE.items():
            for s in specs:
                for token in s['keywords']:
                    self.assertTrue(token, f'{slug}: empty token')
                    self.assertEqual(token, token.lower(),
                                     f'{slug}: {token!r} not lowercase')
                    self.assertEqual(
                        _tokenize_said_words(token), {token},
                        f'{slug}: {token!r} does not survive the tokenizer')

    def test_no_duplicate_responses(self):
        seen_global = {}
        for slug, specs in NPC_DIALOGUE.items():
            for s in specs:
                texts = s['responses']
                self.assertEqual(
                    len(texts), len(set(texts)),
                    f"duplicate within {slug}/{s['entry_type']}:{s['note'] or '-'}")
                for t in texts:
                    seen_global.setdefault(t, []).append(slug)
        # Cross-corpus duplicates are reported, not failed (per the brief).
        cross = {t: slugs for t, slugs in seen_global.items()
                 if len(set(slugs)) > 1}
        if cross:
            print('cross-NPC duplicate responses (report-only):')
            for t, slugs in cross.items():
                print(f'  {sorted(set(slugs))}: {t[:60]}...')

    def test_144_coverage(self):
        for slug in THE_SIX:
            self.assertIn(slug, NPC_DIALOGUE)
            self.assertGreaterEqual(
                len(entries(slug, DialogueEntry.ENTRY_KEYWORD)), 3, slug)

    def test_silent_roster(self):
        for slug in SILENT:
            self.assertNotIn(slug, NPC_DIALOGUE)

    def test_connectives(self):
        for pc in (DialogueConnective.POSITION_SECOND,
                   DialogueConnective.POSITION_LATER):
            pool = DIALOGUE_CONNECTIVES[pc]
            self.assertGreaterEqual(len(pool), 6, pc)
            self.assertEqual(len(pool), len(set(pool)), pc)
            for template in pool:
                self.assertIn('{name}', template, template)


class RenderRuleTests(SimpleTestCase):

    def test_render_rule(self):
        self.assertEqual(
            npc_voice.dialogue_line(DialogueEntry.ENTRY_KEYWORD, 'Name', 'text'),
            ('Name: text', 'say'))
        self.assertEqual(
            npc_voice.dialogue_line(DialogueEntry.ENTRY_GREETING, 'Name', 'text'),
            ('text', 'room'))
        self.assertEqual(
            npc_voice.dialogue_line(DialogueEntry.ENTRY_DEPARTED, 'Name', 'text'),
            ('text', 'room'))

    def test_render_rule_lockstep(self):
        # The npc_voice literal can never drift from the model constant.
        self.assertEqual(npc_voice.SPEECH_ENTRY_TYPES,
                         (DialogueEntry.ENTRY_KEYWORD,))

    def test_connective_gating(self):
        src = inspect.getsource(TickCommand.deliver_dialogue_response)
        self.assertIn('SPEECH_ENTRY_TYPES', src)
        self.assertNotIn("f'{npc_name}: ", src)
        self.assertNotIn('f"{npc_name}: ', src)

    def test_seed_call_ordering(self):
        # The fresh-database trap (brief 5 §2.4): dialogue resolves NPC
        # definitions by slug, so it must seed after the ridge stages.
        src = inspect.getsource(SeedCommand.handle)
        self.assertGreater(src.index('_seed_dialogue()'),
                           src.index('_seed_ridge_npcs()'))
