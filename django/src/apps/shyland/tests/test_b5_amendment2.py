"""v22 Brief 5 Amendment 2 — Spend Block and Display Trims (#131).

The in-combat spend gate (the first generic in-combat refusal), the
blank-line grouping of the stats Armor row, and (in the rewritten
test_b5_amendment1) the removal of the incoming (-N) parenthetical.
"""

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase
from django.utils import timezone

from apps.shyland.models import (
    Character, CombatSession, NpcDefinition, NpcInstance,
)

from .test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)


def make_spend_char(prefix, in_combat=False):
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    Character.objects.filter(pk=char.pk).update(
        unspent_stat_points=2, vitality_current=67, vitality_max=135,
        longevity_current=67, longevity_max=135)
    if in_combat:
        definition = NpcDefinition.objects.create(
            name=f'{prefix} beetle', slug=f'{prefix}-beetle',
            description='x', genre_tag='fantasy',
            base_vitality=50, base_str=1, base_dex=1, base_end=1,
            base_int=1, base_wis=1, base_per=1,
        )
        npc = NpcInstance.objects.create(
            definition=definition, current_room=room, spawn_room=room,
            vitality_current=50, vitality_max=50,
        )
        session = CombatSession.objects.create(
            room=room, last_tick_at=timezone.now())
        session.characters.add(char)
        session.npcs.add(npc)
    return Character.objects.select_related('user').get(pk=char.pk)


class SpendCombatGateTests(TransactionTestCase):

    async def test_in_combat_refuses_and_mutates_nothing(self):
        char = await sync_to_async(make_spend_char)('sgA', in_combat=True)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('1 end')

        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], "You can't do that while in combat.")
        self.assertEqual(msgs[0]['category'], 'warn')

        def state():
            c = Character.objects.get(pk=char.pk)
            return (c.stat_end, c.unspent_stat_points,
                    c.vitality_current, c.vitality_max,
                    c.longevity_current, c.longevity_max)
        self.assertEqual(await sync_to_async(state)(),
                         (10, 2, 67, 135, 67, 135))

    async def test_gate_precedes_validation_output(self):
        # Even garbage arguments get the combat refusal, nothing else.
        char = await sync_to_async(make_spend_char)('sgB', in_combat=True)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('gibberish nonsense')
        msgs = outputs(sent)
        self.assertEqual([m['text'] for m in msgs],
                         ["You can't do that while in combat."])

    async def test_out_of_combat_unchanged_fraction_preserving(self):
        char = await sync_to_async(make_spend_char)('sgC')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('1 end')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('You spend 1 point on Endurance.', texts)

        def state():
            c = Character.objects.get(pk=char.pk)
            return (c.stat_end, c.vitality_current, c.vitality_max)
        end, vit_c, vit_m = await sync_to_async(state)()
        self.assertEqual(end, 11)
        self.assertEqual((vit_c, vit_m), (72, 145))   # bar law, no refill


class StatsSpacingTests(TransactionTestCase):

    def _raw_lines(self, sent):
        for msg in sent:
            if msg.get('type') == 'output' and 'lines' in msg:
                return msg['lines']
        return []

    async def test_exactly_one_blank_between_per_and_armor(self):
        def setup():
            zone, room = make_world('ssA')
            return make_character('ssA', room)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()
        lines = self._raw_lines(sent)
        self.assertTrue(lines)

        per_i = next(i for i, l in enumerate(lines)
                     if 'Perception' in l.get('v', ''))
        armor_i = next(i for i, l in enumerate(lines)
                       if l.get('v', '').strip().startswith('Armor:'))
        # One blank entry between PER and Armor — the row is its own group.
        self.assertEqual(armor_i, per_i + 2)
        self.assertEqual(lines[per_i + 1], {})
        # The pre-existing single blank after the block still follows
        # Armor (then Vitality) — no extra trailing blank.
        self.assertEqual(lines[armor_i + 1], {})
        self.assertIn('Vitality', lines[armor_i + 2].get('v', ''))
