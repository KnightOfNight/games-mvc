"""v24.20 Brief 1 (#203): examine binding rows removal.

Both binding prose rows are deleted from examine's identified detail
block — the `Note:` not-yet-bound row and the `Bound:` bound-to-you row.
Bound state is carried solely by the headline's trailing flag block
([Rarity, Bound|Unbound]); the `Equipped:` and `Curse:` rows are
explicitly untouched.
"""

from django.test import TestCase

from apps.shyland.item_utils import generate_item_instance
from apps.shyland.models import ItemDefinition

from .test_command_revamp import make_character, make_stub_consumer, make_world


def make_def(**overrides):
    fields = dict(
        name='Test Sabre', slug='test-sabre', item_type='weapon',
        genre_tag='fantasy', valid_slots=['MAIN_HAND'],
        scaling_base=5.0, scaling_factor=2.0, damage_spread=3.0,
        primary_stats=[{'stat': 'str', 'base': 1.0, 'factor': 3.0}],
        secondary_stat_pool=[],
    )
    fields.update(overrides)
    return ItemDefinition.objects.create(**fields)


class ExamineBindingRowsRemovalTests(TestCase):

    def detail_lines(self, **state):
        zone, room = make_world('br')
        char = make_character('br', room)
        defn = make_def()
        inst = generate_item_instance(defn, 1, 'common', owner=char)
        for field, value in state.items():
            setattr(inst, field, value)
        inst.save()
        consumer = make_stub_consumer(char, [])
        return consumer._format_identified_item_lines(inst)

    def test_unbound_unequipped_has_no_note_row(self):
        lines = self.detail_lines()
        for line in lines:
            self.assertNotIn('Note:', line)
            self.assertNotIn('not yet bound', line)
        # The headline still carries the fact in its flag block.
        self.assertTrue(lines[0].endswith('Unbound]'))

    def test_soulbound_unequipped_has_no_bound_prose_row(self):
        lines = self.detail_lines(is_soulbound=True)
        for line in lines:
            self.assertNotIn('This item is bound to you.', line)
        self.assertTrue(lines[0].endswith(', Bound]'))

    def test_soulbound_equipped_keeps_equipped_row_no_binding_prose(self):
        lines = self.detail_lines(
            is_soulbound=True, is_equipped=True, equipped_slot='MAIN_HAND')
        self.assertTrue(any(line.startswith('  Equipped:   ')
                            for line in lines))
        for line in lines:
            self.assertNotIn('Note:', line)
            self.assertNotIn('not yet bound', line)
            self.assertNotIn('This item is bound to you.', line)
        self.assertTrue(lines[0].endswith(', Bound]'))

    def test_curse_row_unchanged(self):
        lines = self.detail_lines(is_cursed=True, curse_identified=True)
        self.assertIn('  Curse:      This item carries a curse.', lines)
