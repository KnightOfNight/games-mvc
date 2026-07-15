"""v20 brief 5 (#24/#15): NPC display composition and command echo.

DB-free: unsaved model instances exercise npc_display / npc_display_name
and the grammar's composed-reference matching; the echo path is covered
in test_dispatch_guard (it asserts echo-then-result ordering).
"""
from unittest import mock

from django.test import SimpleTestCase

from apps.shyland.combat_utils import (
    get_unarmed_message, npc_display, npc_display_name,
)
from apps.shyland.command_grammar import resolve
from apps.shyland.models import NpcDefinition, NpcInstance


def make_npc(pk, name, article='the', plural_phrase=''):
    definition = NpcDefinition(pk=pk, name=name, article=article,
                               plural_phrase=plural_phrase)
    npc = NpcInstance(pk=pk + 100, mk_tier=1, vitality_current=10, vitality_max=10)
    npc.definition = definition
    return npc


class NpcDisplayTests(SimpleTestCase):

    def test_article_name(self):
        npc = make_npc(1, 'Silk Matron')
        self.assertEqual(npc_display(npc), 'the Silk Matron')
        self.assertEqual(npc_display(npc, capitalize=True), 'The Silk Matron')

    def test_indefinite_article(self):
        npc = make_npc(2, 'Verdant Shard', article='a')
        self.assertEqual(npc_display(npc), 'a Verdant Shard')
        self.assertEqual(npc_display(npc, capitalize=True), 'A Verdant Shard')

    def test_proper_noun_blank_article(self):
        npc = make_npc(3, 'Morra', article='')
        self.assertEqual(npc_display(npc), 'Morra')
        self.assertEqual(npc_display(npc, capitalize=True), 'Morra')

    def test_plural_phrase_verbatim(self):
        npc = make_npc(4, "Matron's brood",
                       plural_phrase="one of the Matron's brood")
        self.assertEqual(npc_display(npc), "one of the Matron's brood")
        self.assertEqual(npc_display(npc, capitalize=True),
                         "One of the Matron's brood")

    def test_accepts_definition_directly(self):
        definition = NpcDefinition(name='cave spider', article='the')
        self.assertEqual(npc_display(definition), 'the cave spider')

    def test_ordinals_between_article_and_name(self):
        a = make_npc(10, 'cave spider')
        b = make_npc(11, 'cave spider')
        npcs = [a, b]
        self.assertEqual(npc_display_name(a, npcs), 'the first cave spider')
        self.assertEqual(npc_display_name(b, npcs, capitalize=True),
                         'The second cave spider')

    def test_no_ordinal_when_unique(self):
        a = make_npc(12, 'cave spider')
        self.assertEqual(npc_display_name(a, [a]), 'the cave spider')

    def test_plural_phrase_never_takes_ordinal(self):
        a = make_npc(13, "Matron's brood",
                     plural_phrase="one of the Matron's brood")
        b = make_npc(14, "Matron's brood",
                     plural_phrase="one of the Matron's brood")
        self.assertEqual(npc_display_name(a, [a, b]),
                         "one of the Matron's brood")
        self.assertEqual(npc_display_name(b, [a, b]),
                         "one of the Matron's brood")

    def test_proper_noun_never_takes_ordinal(self):
        a = make_npc(15, 'Morra', article='')
        b = make_npc(16, 'Morra', article='')
        self.assertEqual(npc_display_name(a, [a, b]), 'Morra')


class UnarmedFallbackTests(SimpleTestCase):

    def test_fallback_does_not_prepend_article(self):
        # Empty pool + missing fallback pool: the hard-coded fallback must
        # use the composed attacker reference verbatim.
        pool = mock.Mock()
        pool.messages.all.return_value = []
        with mock.patch('apps.shyland.models.UnarmedMessagePool') as pool_model:
            pool_model.DoesNotExist = Exception
            pool_model.objects.prefetch_related.return_value.get.side_effect = \
                pool_model.DoesNotExist
            text = get_unarmed_message(pool, 'you',
                                       attacker_name='The Silk Matron')
        self.assertEqual(text, 'The Silk Matron strikes you.')

    def test_template_substitutes_composed_attacker(self):
        message = mock.Mock()
        message.template = '{attacker} blurs sideways and strikes at {target}, fangs first.'
        pool = mock.Mock()
        pool.messages.all.return_value = [message]
        text = get_unarmed_message(pool, 'you',
                                   attacker_name="One of the Matron's brood")
        self.assertEqual(
            text,
            "One of the Matron's brood blurs sideways and strikes at you, fangs first.",
        )


class GrammarComposedReferenceTests(SimpleTestCase):
    """Additions to the #22 suite (the 30-case table is untouched):
    matching and disambiguation over composed NPC references."""

    def test_attack_with_typed_article(self):
        matron = make_npc(20, 'Silk Matron')
        res = resolve('attack', 'the silk matron', [matron])
        self.assertTrue(res.ok)
        self.assertEqual(res.items, [matron])

    def test_attack_brood_via_phrase_token(self):
        brood = make_npc(21, "Matron's brood",
                         plural_phrase="one of the Matron's brood")
        res = resolve('attack', 'brood', [brood])
        self.assertTrue(res.ok)

    def test_disambiguation_lists_composed_names(self):
        matron = make_npc(22, 'Silk Matron')
        brood = make_npc(23, "Matron's brood",
                         plural_phrase="one of the Matron's brood")
        res = resolve('attack', 'matron', [matron, brood])
        self.assertFalse(res.ok)
        self.assertEqual(res.error, 'ambiguous')
        self.assertIn('the Silk Matron', res.message)
        self.assertIn("one of the Matron's brood", res.message)
