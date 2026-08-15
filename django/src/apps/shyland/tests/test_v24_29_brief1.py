"""v24.29 Brief 1 — plunder, the verification harness, and #250.

Three things sharing a release and no code:

- ``plunder [on|off]`` (#235), the fourth settings command: the
  rights-scoped corpse sweep, run automatically at the moment combat
  ends. The setting, the trigger anchored to ``Combat has ended.``, the
  silence contract, and output identity with the typed sweep.
- The read-only verification harness (#249 Part 2): the forced-rollback
  base class and ``verify_ladder``.
- #250: ``_set_echo_mode`` assigned the wrong cached attribute.
"""

import asyncio
from datetime import timedelta
from io import StringIO
from unittest import mock

from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    Character, CombatAction, CombatSession, COMBAT_ROUND_TICKS, Corpse,
    ItemDefinition, ItemInstance,
)
from apps.shyland.verification import VerificationCommand

from .test_combat_state import make_npc, make_npc_definition
from .test_command_revamp import (
    make_character, make_item_def, make_stub_consumer, make_world, outputs,
)
from .test_v245_bare_loot import make_corpse, make_npc_def, sweep_fixtures
from .test_zombie_sessions import ZombieSessionTestCase, make_engine, make_session


def texts_and_categories(sent):
    return [(m['text'], m['category']) for m in outputs(sent)]


ENDED = ("Combat has ended.", 'reward')

# The two refusals that belong to cmd_loot and must never be spoken on
# plunder's behalf (the silence contract, brief §6.3).
NOTHING_TO_LOOT = "There is nothing to loot here."
NOT_YOUR_KILL = "That is not your kill; you may not loot it."


def is_sweep_line(text):
    """Every line the sweep is capable of emitting: the coin and item
    lines, the carry-capacity refusal, and the closing summary."""
    return (text.startswith('You loot ')
            or text.startswith('Looted ')
            or text.startswith("You can't carry any more."))


# ----------------------------------------------------------------------
# The setting (brief §9.1–5)
# ----------------------------------------------------------------------

class PlunderSettingTests(TransactionTestCase):
    """§4: plunder is an ordinary member of the settings family."""

    def setUp(self):
        self.zone, self.room = make_world('pset')
        self.char = make_character('pset', self.room)

    def test_defaults_off(self):
        # §9.1: a newly created character has it off.
        self.assertFalse(self.char.plunder_mode)
        self.assertFalse(Character.objects.get(pk=self.char.pk).plunder_mode)

    async def test_bare_reports_current_state(self):
        # §9.2: the bare form reports, in system color, both ways round.
        char = await sync_to_async(make_character)('pbare', self.room)
        sent = []
        consumer = make_stub_consumer(char, sent)

        await consumer.cmd_plunder('')
        self.assertEqual(texts_and_categories(sent),
                         [('plunder is off.', 'system')])

        sent.clear()
        await consumer.cmd_plunder('on')
        sent.clear()
        await consumer.cmd_plunder('')
        self.assertEqual(texts_and_categories(sent),
                         [('plunder is on.', 'system')])

    async def test_set_confirms_and_persists(self):
        # §9.3: the confirmation line, and the value reaches the row.
        char = await sync_to_async(make_character)('pset2', self.room)
        sent = []
        consumer = make_stub_consumer(char, sent)

        await consumer.cmd_plunder('on')
        self.assertEqual(texts_and_categories(sent),
                         [('plunder is now on.', 'system')])
        fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
        self.assertTrue(fresh.plunder_mode)

        sent.clear()
        await consumer.cmd_plunder('off')
        self.assertEqual(texts_and_categories(sent),
                         [('plunder is now off.', 'system')])
        fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
        self.assertFalse(fresh.plunder_mode)

    async def test_all_six_words_in_mixed_case(self):
        # §9.3: the whole settings vocabulary, both directions, and the
        # casing the shared helper lowercases for us.
        char = await sync_to_async(make_character)('pwords', self.room)
        sent = []
        consumer = make_stub_consumer(char, sent)

        for word, expected in [('on', True), ('YES', True), ('True', True),
                               ('off', False), ('NO', False), ('False', False)]:
            sent.clear()
            await consumer.cmd_plunder(word)
            fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
            self.assertEqual(fresh.plunder_mode, expected, msg=word)
            state = 'on' if expected else 'off'
            self.assertEqual(texts_and_categories(sent),
                             [(f'plunder is now {state}.', 'system')], msg=word)
            # The cached attribute keeps step with the row.
            self.assertEqual(consumer.character.plunder_mode, expected, msg=word)

    async def test_invalid_input_answers_usage_and_changes_nothing(self):
        # §9.4: the CLI-error layer, in error color, with no write.
        char = await sync_to_async(make_character)('pbad', self.room)
        await sync_to_async(Character.objects.filter(pk=char.pk).update)(
            plunder_mode=True)
        char.plunder_mode = True
        sent = []
        consumer = make_stub_consumer(char, sent)

        await consumer.cmd_plunder('banana')
        self.assertEqual(texts_and_categories(sent),
                         [('Usage: plunder [on|off]', 'error')])
        fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
        self.assertTrue(fresh.plunder_mode)


class PlunderRegistrationTests(SimpleTestCase):
    """§4.6: the registration sites. A settings command is registered in
    five places; the fifth (GDD §9.1) landed with the design session."""

    def test_command_table(self):
        self.assertEqual(SkylandConsumer.COMMAND_TABLE.get('plunder'),
                         ('cmd_plunder', True))

    def test_allowed_while_dying(self):
        # §9.5: it is a setting, so the dying gate lets it through.
        self.assertIn('plunder', SkylandConsumer.DYING_ALLOWED)

    def test_allowed_in_combat(self):
        # §4.6: deliberately NOT in COMBAT_BLOCKED — flipping it
        # mid-fight governs that same fight.
        self.assertNotIn('plunder', SkylandConsumer.COMBAT_BLOCKED)

    def test_help_settings_row_sits_between_echo_and_timestamps(self):
        settings_rows = next(
            rows for title, rows in SkylandConsumer.HELP_SECTIONS
            if title == 'Settings commands'
        )
        names = [row[0] for row in settings_rows]
        self.assertEqual(names.index('plunder'), names.index('echo') + 1)
        self.assertEqual(names.index('timestamps'), names.index('plunder') + 1)
        row = settings_rows[names.index('plunder')]
        self.assertEqual(row[1], 'plunder [on|off]')
        self.assertIn('Default: off.', row[2])

    def test_reaches_the_connect_time_verb_list(self):
        # The verbs payload derives from COMMAND_TABLE and plunder is not
        # an admin verb, so it ships to every client.
        self.assertIn('plunder', SkylandConsumer.COMMAND_TABLE)
        self.assertNotIn('plunder', SkylandConsumer.ADMIN_VERBS)


class PlunderTabCompletionTests(TransactionTestCase):
    """§4.6 site 4: the boolean words offer after the verb."""

    async def test_completes_the_boolean_words(self):
        zone, room = await sync_to_async(make_world)('ptab')
        char = await sync_to_async(make_character)('ptab', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.handle_complete('plunder ')
        payload = [m for m in sent if m.get('type') == 'complete'][-1]
        self.assertEqual(sorted(payload['options']),
                         sorted(SkylandConsumer.SETTING_WORDS))


# ----------------------------------------------------------------------
# The trigger (brief §9.6–11)
# ----------------------------------------------------------------------

class PlunderTriggerTests(ZombieSessionTestCase):
    """§6: plunder fires wherever `Combat has ended.` is delivered, and
    nowhere else."""

    def setUp(self):
        self.zone, self.room = make_world('ptrig')
        self.char = make_character('ptrig', self.room)
        self.definition = make_npc_definition('ptrig')
        self.corpse_def = make_npc_def('ptrig', 'ptrig boar')
        self.item_def = make_item_def('ptrig', 'Ptrig Fang')

    def plunder_on(self, char=None):
        char = char or self.char
        Character.objects.filter(pk=char.pk).update(plunder_mode=True)
        char.plunder_mode = True

    def place_corpse(self, killer=None, copper=25, with_item=True):
        corpse = make_corpse(self.corpse_def, self.room, killer or self.char,
                             copper_drop=copper)
        if with_item:
            ItemInstance.objects.create(
                definition=self.item_def, corpse=corpse, mk_tier=1,
                rarity='common', durability_current=100.0, is_identified=True,
            )
        return corpse

    def close_by_self_heal(self):
        """Site A: a session holding no living NPCs closes at the loop
        head. No kill, so no new corpse enters the room — the corpse set
        under test is exactly what was placed."""
        npc = make_npc(self.definition, self.room, hp=1)
        session = make_session(self.char, [npc], self.room)
        npc.is_alive = False
        npc.vitality_current = 0
        npc.save(update_fields=['is_alive', 'vitality_current'])
        return self.run_combat_tick()

    def kill_last_npc(self, char=None, extra_npcs=0):
        """Site C: the killer's own session emptied by its last kill."""
        char = char or self.char
        npc = make_npc(self.definition, self.room, hp=1)
        npcs = [npc] + [make_npc(self.definition, self.room, hp=50)
                        for _ in range(extra_npcs)]
        session = make_session(char, npcs, self.room)
        self.queue_kill_round(char, session, npc)
        return self.run_combat_tick(force_hits=True)

    def loot_lines(self, cmd, char=None):
        """Everything the sweep can say, and nothing the fight says."""
        char = char or self.char
        return [(text, category) for text, category in self.texts_to(cmd, char.pk)
                if is_sweep_line(text)]

    def test_fires_at_combat_end_with_plunder_on(self):
        # §9.6: the last kill ends combat, and the sweep follows it.
        self.plunder_on()
        corpse = self.place_corpse()
        before = Character.objects.get(pk=self.char.pk).copper

        cmd = self.kill_last_npc()

        texts = self.texts_to(cmd, self.char.pk)
        self.assertIn(ENDED, texts)
        sweep_at = [i for i, (t, _) in enumerate(texts) if is_sweep_line(t)]
        self.assertTrue(sweep_at, 'the sweep produced no output')
        # Ordering is not cosmetic: the transition is announced, then its
        # consequence.
        self.assertGreater(min(sweep_at), texts.index(ENDED))
        self.assertTrue(any(t.startswith('You loot ') for t, _ in texts))

        # The mutations landed: the item is carried, the coin is banked,
        # and the emptied corpse is gone.
        self.assertTrue(ItemInstance.objects.filter(
            definition=self.item_def, owner=self.char).exists())
        self.assertEqual(Character.objects.get(pk=self.char.pk).copper,
                         before + 25)
        self.assertFalse(Corpse.objects.filter(pk=corpse.pk).exists())

    def test_does_not_fire_with_plunder_off(self):
        # §9.7: the identical scenario, setting off.
        corpse = self.place_corpse()
        before = Character.objects.get(pk=self.char.pk).copper

        cmd = self.kill_last_npc()

        self.assertIn(ENDED, self.texts_to(cmd, self.char.pk))
        self.assertEqual(self.loot_lines(cmd), [])
        corpse.refresh_from_db()
        self.assertEqual(corpse.copper_drop, 25)
        self.assertEqual(
            ItemInstance.objects.filter(corpse=corpse).count(), 1)
        self.assertEqual(Character.objects.get(pk=self.char.pk).copper, before)

    def test_no_mid_fight_plunder(self):
        # §9.8: a kill with other NPCs still alive ends nothing, so the
        # sweep does not run — including for a character with plunder on.
        self.plunder_on()
        corpse = self.place_corpse()

        cmd = self.kill_last_npc(extra_npcs=1)

        self.assertNotIn(ENDED, self.texts_to(cmd, self.char.pk))
        self.assertEqual(self.loot_lines(cmd), [])
        corpse.refresh_from_db()
        self.assertEqual(corpse.copper_drop, 25)
        # The fresh corpse from the kill is untouched too.
        self.assertEqual(Corpse.objects.filter(current_room=self.room).count(), 2)

    def test_rights_are_respected(self):
        # §9.11: the sweep takes only the corpses this character killed.
        other = make_character('ptrig_other', self.room)
        self.plunder_on()
        mine = self.place_corpse()
        theirs = self.place_corpse(killer=other)

        self.kill_last_npc()

        self.assertFalse(Corpse.objects.filter(pk=mine.pk).exists())
        theirs.refresh_from_db()
        self.assertEqual(theirs.copper_drop, 25)
        self.assertEqual(ItemInstance.objects.filter(corpse=theirs).count(), 1)

    def test_silence_contract_when_there_is_nothing_to_sweep(self):
        # §9.12: plunder is silent unless it plunders. No rights-held
        # corpse in the room — the character hears the transition and
        # nothing else. The typed command's refusals belong to cmd_loot.
        other = make_character('ptrig_silent', self.room)
        self.plunder_on()
        self.place_corpse(killer=other)   # present, but not this kill

        cmd = self.close_by_self_heal()

        texts = self.texts_to(cmd, self.char.pk)
        self.assertEqual(texts, [ENDED])
        flat = [t for t, _ in texts]
        self.assertNotIn(NOTHING_TO_LOOT, flat)
        self.assertNotIn(NOT_YOUR_KILL, flat)
        self.assertFalse(any(t.startswith('Looted ') for t in flat))

    def test_silence_contract_with_an_empty_room(self):
        # §9.12, the other half: no corpses at all, same silence.
        self.plunder_on()

        cmd = self.close_by_self_heal()

        texts = self.texts_to(cmd, self.char.pk)
        self.assertEqual(texts, [ENDED])

    def test_disconnected_character_plunders_without_raising(self):
        # §9.15/§6.4: quit is allowed in combat and combat continues after
        # it, so a fight can end for a logged-out character. The
        # group_send reaches an empty group — a no-op, not an error — and
        # the mutations land regardless. Driven through the real
        # transport rather than the recording stub.
        self.plunder_on()
        corpse = self.place_corpse()

        from apps.shyland.management.commands.run_tick_engine import Command
        asyncio.run(Command().deliver_plunder(self.char.pk))

        self.assertFalse(Corpse.objects.filter(pk=corpse.pk).exists())
        self.assertTrue(ItemInstance.objects.filter(
            definition=self.item_def, owner=self.char).exists())


class PlunderExclusionTests(ZombieSessionTestCase):
    """§6.1: flee and death are excluded because the anchor excludes
    them, not because anything guards against them. Verified by test, as
    the brief directs — never coded around."""

    def setUp(self):
        self.zone, self.room = make_world('pexc')
        self.refuge = self.zone.rooms.create(
            name='pexc Refuge', description='Long.', brief_description='Brief.',
            coord_x=0, coord_y=1,
        )
        self.room.exit_north = self.refuge
        self.room.save(update_fields=['exit_north'])
        self.char = make_character('pexc', self.room)
        Character.objects.filter(pk=self.char.pk).update(plunder_mode=True)
        self.char.plunder_mode = True
        self.corpse_def = make_npc_def('pexc', 'pexc boar')
        self.item_def = make_item_def('pexc', 'Pexc Fang')
        self.corpse = make_corpse(self.corpse_def, self.room, self.char,
                                  copper_drop=25)
        ItemInstance.objects.create(
            definition=self.item_def, corpse=self.corpse, mk_tier=1,
            rarity='common', durability_current=100.0, is_identified=True,
        )
        self.definition = make_npc_definition('pexc')

    def test_flee_does_not_plunder(self):
        # §9.9: flee's end path lives in consumers.py and emits no
        # `Combat has ended.` line, so there is nothing for plunder to
        # anchor to.
        npc = make_npc(self.definition, self.room, hp=50)
        session = make_session(self.char, [npc], self.room)
        sent = []
        consumer = make_stub_consumer(self.char, sent)
        consumer.last_direction = None

        # Force the contest: a natural 20 against a 1-PER NPC side.
        with mock.patch('apps.shyland.consumers.random.randint', return_value=20):
            asyncio.run(consumer.cmd_flee())

        session.refresh_from_db()
        self.assertFalse(session.is_active)
        texts = [t for t, _ in texts_and_categories(sent)]
        self.assertNotIn("Combat has ended.", texts)
        self.assertFalse(any(t.startswith('You loot ') for t in texts))
        self.assertFalse(any(t.startswith('Looted ') for t in texts))
        # The corpse the character had rights to is still whole.
        self.corpse.refresh_from_db()
        self.assertEqual(self.corpse.copper_drop, 25)
        self.assertEqual(
            ItemInstance.objects.filter(corpse=self.corpse).count(), 1)

    def test_death_does_not_plunder(self):
        # §9.10: a dying character is removed from its session before the
        # session can close, so no combat-end line reaches them.
        self.char.vitality_current = 1
        self.char.save(update_fields=['vitality_current'])
        npc = make_npc(self.definition, self.room, hp=500)
        npc.definition.base_str = 500
        npc.definition.save(update_fields=['base_str'])
        session = make_session(self.char, [npc], self.room)
        session.tick_counter = COMBAT_ROUND_TICKS - 1
        session.save(update_fields=['tick_counter'])

        cmd = self.run_combat_tick(force_hits=True)

        self.assertTrue(Character.objects.get(pk=self.char.pk).is_dying)
        texts = self.texts_to(cmd, self.char.pk)
        self.assertNotIn(ENDED, texts)
        self.assertFalse(any(t.startswith('You loot ') for t, _ in texts))
        self.assertFalse(any(t.startswith('Looted ') for t, _ in texts))
        self.corpse.refresh_from_db()
        self.assertEqual(self.corpse.copper_drop, 25)


# ----------------------------------------------------------------------
# Output identity (brief §9.13–14)
# ----------------------------------------------------------------------

class PlunderOutputIdentityTests(ZombieSessionTestCase):
    """§6.5: a plunder must be indistinguishable from a `loot` the player
    typed. Built as a direct comparison of the two sequences rather than
    two hand-written expectations."""

    def test_plunder_output_is_the_typed_sweep_output(self):
        # §9.13. sweep_fixtures builds a corpse carrying coin and an item
        # plus an empty-handed one, so the comparison covers the coin
        # line, the item line, the 'carried nothing' clause, and the
        # summary — and rebuild() recreates the identical set.
        char, rebuild = sweep_fixtures('pid')
        Character.objects.filter(pk=char.pk).update(plunder_mode=True)
        char.plunder_mode = True

        definition = make_npc_definition('pid')
        npc = make_npc(definition, char.current_room, hp=1)
        session = make_session(char, [npc], char.current_room)
        npc.is_alive = False
        npc.vitality_current = 0
        npc.save(update_fields=['is_alive', 'vitality_current'])
        cmd = self.run_combat_tick()
        plunder_lines = [t for t in self.texts_to(cmd, char.pk) if t != ENDED]

        # The same corpse set again, this time looted by hand.
        rebuild()
        char.refresh_from_db()
        sent = []
        consumer = make_stub_consumer(char, sent)
        asyncio.run(consumer.cmd_loot(''))
        typed_lines = texts_and_categories(sent)

        self.assertEqual(plunder_lines, typed_lines)
        self.assertTrue(plunder_lines, 'the comparison must not be vacuous')

    def test_carry_capacity_refusal_fires_mid_sweep(self):
        # §9.14: filling up mid-plunder emits the same warn the typed
        # sweep does, and stops there.
        zone, room = make_world('pcap')
        char = make_character('pcap', room)
        Character.objects.filter(pk=char.pk).update(
            plunder_mode=True, stat_str=1)
        char.refresh_from_db()

        filler = make_item_def('pcap', 'Pcap Pebble')
        for _ in range(9):        # capacity is STR x 10 = 10
            ItemInstance.objects.create(
                definition=filler, owner=char, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )

        corpse_def = make_npc_def('pcap', 'pcap boar')
        corpse = make_corpse(corpse_def, room, char, copper_drop=0)
        loot_def = make_item_def('pcap', 'Pcap Fang')
        for _ in range(3):
            ItemInstance.objects.create(
                definition=loot_def, corpse=corpse, mk_tier=1, rarity='common',
                durability_current=100.0, is_identified=True,
            )

        definition = make_npc_definition('pcap')
        npc = make_npc(definition, room, hp=1)
        make_session(char, [npc], room)
        npc.is_alive = False
        npc.vitality_current = 0
        npc.save(update_fields=['is_alive', 'vitality_current'])

        cmd = self.run_combat_tick()
        texts = [t for t, _ in self.texts_to(cmd, char.pk)]

        self.assertIn("You can't carry any more. (10/10 items)", texts)
        # Exactly one item was taken before the refusal, and the rest
        # stayed on the corpse — nothing silently eaten.
        self.assertEqual(
            ItemInstance.objects.filter(definition=loot_def, owner=char).count(), 1)
        self.assertEqual(
            ItemInstance.objects.filter(corpse=corpse).count(), 2)


# ----------------------------------------------------------------------
# The verification harness (brief §9.16–20)
# ----------------------------------------------------------------------

class _WritingVerification(VerificationCommand):
    """A verification body that writes. It must not stick."""

    def verify(self, *args, **options):
        Character.objects.filter(pk=options['target_pk']).update(copper=999999)
        # Proof the write really happened inside the block, so the
        # assertion afterwards is about the rollback and not about a
        # write that never ran.
        assert Character.objects.get(pk=options['target_pk']).copper == 999999
        return []


class ForcedRollbackTests(TransactionTestCase):
    """§7.1: the runtime backstop behind the verify_* name gate."""

    def test_a_write_inside_a_verification_is_discarded(self):
        # §9.16.
        zone, room = make_world('vroll')
        char = make_character('vroll', room)
        Character.objects.filter(pk=char.pk).update(copper=7)

        _WritingVerification().handle(target_pk=char.pk)

        self.assertEqual(Character.objects.get(pk=char.pk).copper, 7)

    def test_findings_exit_nonzero(self):
        # §7.1: the outcome signal. CommandError is Django's nonzero-exit
        # mechanism — it raises under call_command and exits 1 under
        # run_from_argv, so make sees the failure.
        class _Findings(VerificationCommand):
            def verify(self, *args, **options):
                return ['something is wrong']

        with self.assertRaises(CommandError):
            _Findings(stdout=StringIO()).handle()


class VerifyLadderTests(TransactionTestCase):
    """§7.2: the survey V24.28 Brief 1 §7 step 8 specified and could not
    run — ItemInstance rows whose mk_tier falls outside their rung."""

    def setUp(self):
        self.zone, self.room = make_world('vlad')
        self.char = make_character('vlad', self.room)
        # A bounded rung: copper, Mk 1 only.
        self.copper_def = make_item_def('vlad', 'Vlad Copper Mace')
        ItemDefinition.objects.filter(pk=self.copper_def.pk).update(
            tier_material_mk_min=1, tier_material_mk_max=1)
        self.copper_def.refresh_from_db()

    def make_instance(self, definition, mk_tier):
        return ItemInstance.objects.create(
            definition=definition, owner=self.char, mk_tier=mk_tier,
            rarity='common', durability_current=100.0, is_identified=True,
        )

    def run_verify(self):
        out = StringIO()
        call_command('verify_ladder', stdout=out)
        return out.getvalue()

    def test_clean_database_reports_zero_and_exits_zero(self):
        # §9.17: no exception raised is the exit-0 signal.
        self.make_instance(self.copper_def, 1)
        output = self.run_verify()
        self.assertIn('0 mismatched instance(s) out of 1 ladder row(s).', output)

    def test_mismatch_is_reported_and_left_in_place(self):
        # §9.18: it reports, it does not repair.
        self.make_instance(self.copper_def, 1)
        rogue = self.make_instance(self.copper_def, 5)

        out = StringIO()
        with self.assertRaises(CommandError):
            call_command('verify_ladder', stdout=out)
        output = out.getvalue()

        self.assertIn('1 mismatched instance(s) out of 2 ladder row(s).', output)
        self.assertIn(self.copper_def.slug, output)
        self.assertIn('Mk 5', output)
        # The offending row survives the report.
        self.assertTrue(ItemInstance.objects.filter(pk=rogue.pk).exists())
        self.assertEqual(ItemInstance.objects.get(pk=rogue.pk).mk_tier, 5)

    def test_null_maximum_is_unbounded_not_zero(self):
        # §9.19: sphaerium's rung spans upward forever.
        sphaerium = make_item_def('vlad', 'Vlad Sphaerium Mace')
        ItemDefinition.objects.filter(pk=sphaerium.pk).update(
            tier_material_mk_min=8, tier_material_mk_max=None)
        sphaerium.refresh_from_db()
        self.make_instance(sphaerium, 99)

        output = self.run_verify()

        self.assertIn('0 mismatched instance(s) out of 1 ladder row(s).', output)

    def test_non_ladder_definition_is_not_counted(self):
        # §9.20: a null minimum means not on the ladder at all — the
        # freebie kit suppresses its Mk suffix without joining.
        freebie = make_item_def('vlad', 'Vlad Freebie Shiv')
        self.assertIsNone(freebie.tier_material_mk_min)
        self.make_instance(freebie, 99)

        output = self.run_verify()

        self.assertIn('0 mismatched instance(s) out of 0 ladder row(s).', output)


# ----------------------------------------------------------------------
# #250 (brief §9.21–22)
# ----------------------------------------------------------------------

class EchoSetterTests(TransactionTestCase):
    """§4.5: _set_echo_mode assigned show_timestamps. The DB write was
    always right, so the defect was latent — but it corrupted the cached
    attribute on every echo change."""

    async def test_echo_no_longer_touches_the_cached_show_timestamps(self):
        # §9.21: assert on the CACHED attribute specifically. A test that
        # only reads a fresh fetch would pass against the bug.
        zone, room = await sync_to_async(make_world)('echo1')
        char = await sync_to_async(make_character)('echo1', room)
        sent = []
        consumer = make_stub_consumer(char, sent)

        for word in ('off', 'on'):
            await consumer.cmd_echo(word)
            fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
            self.assertEqual(consumer.character.show_timestamps,
                             fresh.show_timestamps, msg=word)
            # And the setting it was clobbering keeps its own value.
            self.assertTrue(consumer.character.show_timestamps, msg=word)

    async def test_echo_still_behaves(self):
        # §9.22: the fix removed a line; it removed no behavior.
        zone, room = await sync_to_async(make_world)('echo2')
        char = await sync_to_async(make_character)('echo2', room)
        sent = []
        consumer = make_stub_consumer(char, sent)

        await consumer.cmd_echo('')
        self.assertEqual(texts_and_categories(sent),
                         [('command echo is on.', 'system')])

        for word, expected in [('off', False), ('YES', True), ('False', False),
                               ('on', True), ('no', False), ('true', True)]:
            sent.clear()
            await consumer.cmd_echo(word)
            fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
            self.assertEqual(fresh.echo_mode, expected, msg=word)
            self.assertEqual(consumer.character.echo_mode, expected, msg=word)
            state = 'on' if expected else 'off'
            texts = [t for t, _ in texts_and_categories(sent)]
            self.assertIn(f'command echo is now {state}.', texts)
            # The status payload carries the new value to the client.
            status = [m for m in sent if m.get('type') == 'status'][-1]
            self.assertEqual(status['echo_mode'], expected, msg=word)
