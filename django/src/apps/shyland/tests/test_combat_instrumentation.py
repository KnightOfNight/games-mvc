"""V25.2 Brief 1 (#33): combat instrumentation — the combat_* family.

Pins the seven-kind family (GDD §10.11): the detailed helper variants'
equivalence guarantee (same value, same random-stream consumption as the
plain names), the combat_start/combat_join snapshots, envelope
discipline (audience=[] always; NPC-acted records carry actor_id=None
with pks in data), internals-first ordering (a round's records emit
before its player-facing sends), the combat_end outcome/reason mapping
at every end site, the fall/death two-phase records, and the ≤16-char
kind-length invariant.

mc.mc_emit is replaced by test_mc_sink's EmitRecorder pattern — nothing
here touches a live stream.
"""
import asyncio
import random
from datetime import timedelta
from unittest import mock

from asgiref.sync import sync_to_async
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland import combat_utils
from apps.shyland.models import (
    Character, CombatAction, CombatSession, COMBAT_ROUND_TICKS,
    DYING_DURATION_SECS, MCEvent, NpcEffect, STALE_SESSION_SECS,
)

from .test_combat_state import (
    make_character, make_heal_definition, make_npc, make_npc_definition,
    make_world,
)
from .test_command_revamp import make_stub_consumer
from .test_mc_sink import EmitRecorder
from .test_zombie_sessions import make_engine, make_session

ALL_KINDS = ('combat_start', 'combat_join', 'combat_round', 'combat_action',
             'combat_flee', 'combat_death', 'combat_end')


class FakeDefinition:
    def __init__(self, is_ranged=False):
        self.is_ranged = is_ranged
        self.takes_durability_loss = False
        self.durability_table = []


class FakeWeapon:
    """Attribute-shaped stand-in for an equipped weapon ItemInstance —
    composite_weapon_term reads attributes only."""
    def __init__(self, pk, slot, midpoint, spread, ranged=False):
        self.pk = pk
        self.definition_id = pk * 10
        self.equipped_slot = slot
        self.damage_midpoint = midpoint
        self.damage_spread = spread
        self.definition = FakeDefinition(ranged)
        self.durability_current = 100.0


class FakeGearItem:
    """Attribute-shaped stand-in for roll_gear_bonus_damage — it reads
    the two rolled-stats lists only."""
    def __init__(self, primary=None, secondary=None):
        self.rolled_primary_stats = primary or []
        self.rolled_secondary_stats = secondary or []


class EquivalencePinTests(SimpleTestCase):
    """§6.1: under the same seed, plain == detailed[0] and the random
    stream is consumed identically (random.getstate() matches after)."""

    def pin(self, plain, detailed, *args, seed=1234, **kwargs):
        random.seed(seed)
        plain_value = plain(*args, **kwargs)
        plain_state = random.getstate()
        random.seed(seed)
        detailed_value, detail = detailed(*args, **kwargs)
        detailed_state = random.getstate()
        self.assertEqual(plain_value, detailed_value)
        self.assertEqual(plain_state, detailed_state)
        return detail

    def test_roll_initiative_equivalence(self):
        detail = self.pin(combat_utils.roll_initiative,
                          combat_utils.roll_initiative_detailed, 12, 9)
        self.assertEqual(detail['dex'], 12)
        self.assertEqual(detail['per'], 9)
        self.assertEqual(detail['total'], 12 + 9 + detail['die'])

    def test_resolve_hit_equivalence(self):
        # Several seeds so both the success branch (extra crit roll) and
        # the miss branch (single roll) are pinned.
        for seed in range(20):
            self.pin(combat_utils.resolve_hit,
                     combat_utils.resolve_hit_detailed,
                     10, 8, crit_bonus=0.05, seed=seed)

    def test_calculate_damage_equivalence(self):
        detail = self.pin(combat_utils.calculate_damage,
                          combat_utils.calculate_damage_detailed,
                          20.0, 5, 1.2, 1.0, 'critical', is_focus_target=True)
        self.assertEqual(detail['hit_multiplier'], 1.5)
        self.assertEqual(detail['effective_acuity'], 1.2)
        self.assertEqual(detail['final'], detail['raw'] * 1.5)

    def test_composite_weapon_term_equivalence(self):
        weapons = [FakeWeapon(1, 'MAIN_HAND', 10.0, 2.0),
                   FakeWeapon(2, 'OFF_HAND', 6.0, 1.0),
                   FakeWeapon(3, 'RANGED', 8.0, 3.0, ranged=True)]
        detail = self.pin(combat_utils.composite_weapon_term,
                          combat_utils.composite_weapon_term_detailed,
                          weapons, 15, 11)
        self.assertEqual(detail['primary_slot'], 'MAIN_HAND')
        self.assertEqual(len(detail['weapons']), 3)
        rows = {r['instance']: r for r in detail['weapons']}
        self.assertEqual(rows[1]['factor'], 1.0)
        self.assertEqual(rows[2]['factor'], 0.5)
        self.assertEqual(rows[3]['stat'], 11)   # ranged reads DEX
        self.assertEqual(rows[1]['stat'], 15)   # melee reads STR

    def test_roll_gear_bonus_damage_equivalence(self):
        items = [
            FakeGearItem(primary=[{'stat': 'bleed_factor', 'value': 8.0}],
                         secondary=[{'stat': 'electric_damage_bonus', 'value': 3.0}]),
            FakeGearItem(primary=[{'stat': 'stun_factor', 'value': 4.0, 'floor': 2}]),
            FakeGearItem(secondary=[{'stat': 'poison_factor', 'value': 0.0}]),
        ]
        for seed in range(20):
            detail = self.pin(combat_utils.roll_gear_bonus_damage,
                              combat_utils.roll_gear_bonus_damage_detailed,
                              items, seed=seed)
            # One candidate entry per proc-factor stat, fired or not; the
            # zero-value candidate never consumed randomness but is listed.
            self.assertEqual([p['stat'] for p in detail['procs']],
                             ['bleed_factor', 'stun_factor', 'poison_factor'])
            self.assertEqual(detail['flat'], 3.0)
            for proc in detail['procs']:
                self.assertEqual('rolled' in proc, proc['fired'])
            self.assertFalse(detail['procs'][2]['fired'])


class NpcEffectsEquivalenceTests(TransactionTestCase):
    """§6.1: the apply_npc_effects pin runs on a seeded DB fixture."""

    def setUp(self):
        self.zone, self.room = make_world('eqe')
        self.char = make_character('eqe', self.room)
        self.definition = make_npc_definition('eqe')
        self.npc = make_npc(self.definition, self.room)
        for i, chance in enumerate((0.5, 0.5, 0.5)):
            NpcEffect.objects.create(
                npc_definition=self.definition,
                effect_definition=make_heal_definition(f'eqe{i}'),
                effect_chance=chance,
            )

    def test_apply_npc_effects_equivalence(self):
        random.seed(77)
        plain_msgs = combat_utils.apply_npc_effects(self.npc, self.char)
        plain_state = random.getstate()
        random.seed(77)
        detailed_msgs, candidates = combat_utils.apply_npc_effects_detailed(
            self.npc, self.char)
        detailed_state = random.getstate()
        self.assertEqual(plain_msgs, detailed_msgs)
        self.assertEqual(plain_state, detailed_state)
        # Every NpcEffect row is a candidate, fired or not.
        self.assertEqual(len(candidates), 3)
        for c in candidates:
            self.assertEqual(set(c.keys()), {'name', 'chance', 'fired'})
            self.assertEqual(c['chance'], 0.5)


class ResolveHitBranchTests(SimpleTestCase):
    """§6.2: detail contents on every branch, via patched randomness."""

    def test_miss_detail(self):
        with mock.patch('random.randint', return_value=1):
            result, detail = combat_utils.resolve_hit_detailed(0, 10)
        self.assertEqual(result, 'miss')
        self.assertEqual(detail, {'die': 1, 'attack_total': 1, 'defense': 20,
                                  'margin': -19, 'result': 'miss'})

    def test_graze_detail(self):
        with mock.patch('random.randint', return_value=18):
            result, detail = combat_utils.resolve_hit_detailed(0, 10)
        self.assertEqual(result, 'graze')
        self.assertEqual(detail['margin'], -2)
        self.assertNotIn('crit_chance', detail)
        self.assertNotIn('crit_die', detail)

    def test_hit_detail(self):
        with mock.patch('random.randint', return_value=20), \
             mock.patch('random.random', return_value=0.99):
            result, detail = combat_utils.resolve_hit_detailed(5, 5)
        self.assertEqual(result, 'hit')
        self.assertEqual(detail['attack_total'], 25)
        self.assertEqual(detail['defense'], 15)
        self.assertEqual(detail['margin'], 10)
        self.assertEqual(detail['crit_die'], 0.99)
        self.assertEqual(detail['crit_chance'], 0.05)   # floor at CRIT_BASE

    def test_critical_detail(self):
        with mock.patch('random.randint', return_value=20), \
             mock.patch('random.random', return_value=0.0):
            result, detail = combat_utils.resolve_hit_detailed(5, 5, crit_bonus=0.10)
        self.assertEqual(result, 'critical')
        self.assertEqual(detail['result'], 'critical')
        self.assertAlmostEqual(detail['crit_chance'], 0.15)
        self.assertEqual(detail['crit_die'], 0.0)


class KindLengthTests(SimpleTestCase):
    """§6.7: every new kind fits the MCEvent.kind column."""

    def test_all_kinds_fit_the_column(self):
        max_length = MCEvent._meta.get_field('kind').max_length
        for kind in ALL_KINDS:
            self.assertLessEqual(len(kind), max_length, kind)
            self.assertLessEqual(len(kind), 16, kind)


class StartCombatRecordTests(TransactionTestCase):
    """§6.3: create -> combat_start with complete snapshots; join ->
    combat_join with only the new NPCs; nothing new -> no record."""

    def setUp(self):
        self.zone, self.room = make_world('scr')
        self.char = make_character('scr', self.room)
        self.definition = make_npc_definition('scr')
        self.npc_a = make_npc(self.definition, self.room)
        self.npc_b = make_npc(self.definition, self.room)
        self.consumer = make_stub_consumer(self.char, [])

    def start(self, npcs, **kwargs):
        return asyncio.run(self.consumer.start_combat(npcs, **kwargs))

    def test_create_emits_combat_start_with_snapshots(self):
        session, records = self.start(
            [self.npc_a], first_attacker='character',
            focus_npc=self.npc_a, origin='attack')
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['kind'], 'combat_start')
        self.assertEqual(record['actor_id'], self.char.pk)
        self.assertEqual(record['actor_name'], self.char.name)
        self.assertEqual(record['room_id'], self.room.pk)
        self.assertEqual(record['audience'], [])
        data = record['data']
        self.assertEqual(data['session'], session.pk)
        self.assertEqual(data['room'], self.room.pk)
        self.assertEqual(data['zone'], self.zone.name)
        self.assertNotIn('area', data)   # the fixture room has no area
        self.assertEqual(data['origin'], 'attack')
        self.assertEqual(data['first_attacker'], 'character')
        snap = data['character']
        self.assertEqual(set(snap.keys()),
                         {'id', 'name', 'level', 'archetype', 'origin',
                          'stats', 'gear_bonus', 'tav', 'vitality',
                          'acuity', 'longevity'})
        self.assertEqual(snap['id'], self.char.pk)
        self.assertEqual(snap['name'], self.char.name)
        self.assertEqual(set(snap['stats'].keys()),
                         {'str', 'dex', 'end', 'int', 'wis', 'per'})
        self.assertEqual(set(snap['gear_bonus'].keys()),
                         {'str', 'dex', 'end', 'int', 'wis', 'per'})
        self.assertEqual(snap['vitality'],
                         [self.char.vitality_current, self.char.vitality_max])
        self.assertEqual(len(snap['acuity']), 4)
        self.assertEqual(len(data['npcs']), 1)
        npc_snap = data['npcs'][0]
        self.assertEqual(set(npc_snap.keys()),
                         {'instance', 'definition', 'slug', 'name',
                          'combat_tier', 'mk_tier', 'level', 'stats',
                          'vitality'})
        self.assertEqual(npc_snap['instance'], self.npc_a.pk)
        self.assertEqual(npc_snap['definition'], self.definition.pk)
        self.assertEqual(set(npc_snap['stats'].keys()),
                         {'dex', 'str', 'per', 'int'})
        self.assertEqual(npc_snap['vitality'], [20, 20])

    def test_join_emits_combat_join_with_new_npcs_only(self):
        session, _ = self.start([self.npc_a], origin='attack')
        session2, records = self.start([self.npc_a, self.npc_b],
                                       origin='aggro')
        self.assertEqual(session2.pk, session.pk)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['kind'], 'combat_join')
        self.assertEqual(record['audience'], [])
        data = record['data']
        self.assertEqual(data['session'], session.pk)
        self.assertEqual(data['room'], self.room.pk)
        self.assertEqual(data['origin'], 'aggro')
        self.assertEqual([n['instance'] for n in data['npcs']],
                         [self.npc_b.pk])

    def test_nothing_new_emits_nothing(self):
        self.start([self.npc_a], origin='attack')
        session, records = self.start([self.npc_a], origin='aggro')
        self.assertEqual(records, [])


class RoundHarness(TransactionTestCase):
    """Shared driver: one engine tick with mc.mc_emit recorded and the
    transport events interleaved into one sequenced log."""

    def run_tick(self, tick_number=1, resolve_side_effect=None):
        cmd = make_engine()
        events = []   # ('mc', kind, call) | ('send',) | ('broadcast',)
        recorder = EmitRecorder()

        async def rec_emit(kind, **kwargs):
            await recorder(kind, **kwargs)
            events.append(('mc', kind, recorder.calls[-1]))

        orig_send = cmd.send_to_player
        orig_broadcast = cmd.broadcast_to_room

        async def send_wrap(*args, **kwargs):
            events.append(('send',))
            await orig_send(*args, **kwargs)

        async def broadcast_wrap(*args, **kwargs):
            events.append(('broadcast',))
            await orig_broadcast(*args, **kwargs)

        cmd.send_to_player = send_wrap
        cmd.broadcast_to_room = broadcast_wrap

        patches = [mock.patch('apps.shyland.mc.mc_emit', new=rec_emit)]
        if resolve_side_effect is not None:
            patches.append(mock.patch(
                'apps.shyland.combat_utils.resolve_hit_detailed',
                side_effect=resolve_side_effect))
        with patches[0]:
            if len(patches) > 1:
                with patches[1]:
                    asyncio.run(cmd.process_combat(tick_number))
            else:
                asyncio.run(cmd.process_combat(tick_number))
        return cmd, recorder, events

    @staticmethod
    def all_hits(attacker_dex, target_dodge, crit_bonus=None):
        return ('hit', {})

    @staticmethod
    def player_misses_npc_hits(attacker_dex, target_dodge, crit_bonus=None):
        # The player path passes crit_bonus; the NPC path does not.
        return ('miss', {}) if crit_bonus is not None else ('hit', {})


class OrderingAndEnvelopeTests(RoundHarness):
    """§6.4/§6.5: envelope discipline and internals-first ordering."""

    def setUp(self):
        self.zone, self.room = make_world('oe')
        self.char = make_character('oe', self.room)
        Character.objects.filter(pk=self.char.pk).update(
            vitality_current=500, vitality_max=500)
        self.definition = make_npc_definition('oe')
        self.npc = make_npc(self.definition, self.room, hp=1000)
        self.session = make_session(self.char, [self.npc], self.room,
                                    tick_counter=COMBAT_ROUND_TICKS - 1)

    def test_round_records_precede_every_send(self):
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.all_hits)
        mc_indexes = [i for i, e in enumerate(events) if e[0] == 'mc']
        send_indexes = [i for i, e in enumerate(events) if e[0] != 'mc']
        self.assertTrue(mc_indexes, 'no MC records emitted')
        self.assertTrue(send_indexes, 'no player-facing sends fired')
        self.assertLess(max(mc_indexes), min(send_indexes))
        # Round 1: the round record, then the actions in resolution order
        # (first_attacker='character' -> player action, then NPC action).
        kinds = recorder.kinds()
        self.assertEqual(kinds[0], 'combat_round')
        self.assertEqual(kinds[1], 'combat_action')
        self.assertEqual(kinds[2], 'combat_action')
        self.assertEqual(recorder.calls[1]['actor_id'], self.char.pk)
        self.assertIsNone(recorder.calls[2]['actor_id'])

    def test_round_one_record_carries_first_attacker_basis(self):
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.all_hits)
        round_record = recorder.calls[0]
        data = round_record['data']
        self.assertEqual(data['basis'], 'first_attacker')
        self.assertEqual(data['first_attacker'], 'character')
        self.assertEqual(data['round'], 1)
        self.assertNotIn('character_roll', data)
        self.assertNotIn('npc_rolls', data)

    def test_initiative_round_record_carries_the_rolls(self):
        self.session.tick_counter = (2 * COMBAT_ROUND_TICKS) - 1
        self.session.save(update_fields=['tick_counter'])
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.all_hits)
        data = recorder.calls[0]['data']
        self.assertEqual(data['basis'], 'initiative')
        self.assertEqual(data['round'], 2)
        self.assertEqual(set(data['character_roll'].keys()),
                         {'dex', 'per', 'die', 'total'})
        self.assertEqual(len(data['npc_rolls']), 1)
        self.assertEqual(set(data['npc_rolls'][0].keys()),
                         {'instance', 'dex', 'per', 'die', 'total'})
        self.assertIn(data['order'], ('character_first', 'npcs_first'))
        self.assertIsInstance(data['npc_avg'], float)

    def test_envelope_discipline_on_every_record(self):
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.all_hits)
        self.assertTrue(recorder.calls)
        for call in recorder.calls:
            self.assertEqual(call['audience'], [], call['kind'])
            self.assertIn('session', call['data'], call['kind'])
            self.assertEqual(call['room_id'], self.room.pk)
        npc_actions = [c for c in recorder.calls
                       if c['kind'] == 'combat_action'
                       and c['actor_id'] is None]
        self.assertTrue(npc_actions)
        for call in npc_actions:
            self.assertEqual(call['actor_name'], self.definition.name)
            self.assertEqual(call['data']['attacker']['instance'], self.npc.pk)
            self.assertEqual(call['data']['attacker']['definition'],
                             self.definition.pk)

    def test_action_detail_contents(self):
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.all_hits)
        player_action = next(c for c in recorder.calls
                             if c['kind'] == 'combat_action'
                             and c['actor_id'] is not None)
        data = player_action['data']
        self.assertEqual(data['target']['instance'], self.npc.pk)
        self.assertTrue(data['focus'])
        self.assertIn('to_hit', data)
        dmg = data['damage']
        self.assertIn('unarmed_base', dmg)   # the fixture char is unarmed
        self.assertNotIn('weapons', dmg)
        for key in ('stat_bonus', 'acuity_mod', 'hit_multiplier', 'raw', 'final'):
            self.assertIn(key, dmg)
        self.assertEqual(data['gear_bonus'], {'total': 0, 'procs': [], 'flat': 0.0})
        before, after = data['target_vitality']
        self.assertEqual(before, 1000)
        self.assertLess(after, before)

        npc_action = next(c for c in recorder.calls
                          if c['kind'] == 'combat_action'
                          and c['actor_id'] is None)
        dmg = npc_action['data']['damage']
        for key in ('base_roll', 'str_basis', 'hit_multiplier', 'raw',
                    'pre_mitigation', 'tav', 'final'):
            self.assertIn(key, dmg)
        self.assertEqual(npc_action['data']['target_fell'], False)
        self.assertIsInstance(npc_action['data']['effects'], list)


class EndSiteTests(RoundHarness):
    """§6.6: the combat_end outcome/reason mapping at every end site."""

    def setUp(self):
        self.zone, self.room = make_world('es')
        self.char = make_character('es', self.room)
        Character.objects.filter(pk=self.char.pk).update(
            vitality_current=500, vitality_max=500, stat_str=100)
        self.definition = make_npc_definition('es')

    def end_records(self, recorder):
        return [c for c in recorder.calls if c['kind'] == 'combat_end']

    def test_kill_maps_to_win(self):
        npc = make_npc(self.definition, self.room, hp=1)
        session = make_session(self.char, [npc], self.room,
                               tick_counter=COMBAT_ROUND_TICKS - 1)
        CombatAction.objects.create(
            combat_session=session, character=self.char,
            action_type=CombatAction.ACTION_ATTACK, target_npc=npc)
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.all_hits)
        ends = self.end_records(recorder)
        self.assertEqual(len(ends), 1)
        data = ends[0]['data']
        self.assertEqual(data['session'], session.pk)
        self.assertEqual(data['outcome'], 'win')
        self.assertEqual(data['reason'], 'kill')
        self.assertEqual(data['npcs_remaining'], [])
        self.assertEqual(data['rounds'], 1)
        self.assertGreaterEqual(data['duration_secs'], 0.0)
        # The killing action carries the kill fields.
        action = next(c for c in recorder.calls
                      if c['kind'] == 'combat_action'
                      and c['data'].get('kill'))
        self.assertGreater(action['data']['xp'], 0)
        self.assertIsInstance(action['data']['level_ups'], int)

    def test_sibling_kill_maps_to_win(self):
        char_b = make_character('es_b', self.room)
        npc = make_npc(self.definition, self.room, hp=1)
        session_a = make_session(self.char, [npc], self.room,
                                 tick_counter=COMBAT_ROUND_TICKS - 1)
        session_b = make_session(char_b, [npc], self.room)
        CombatAction.objects.create(
            combat_session=session_a, character=self.char,
            action_type=CombatAction.ACTION_ATTACK, target_npc=npc)
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.all_hits)
        by_session = {c['data']['session']: c['data']
                      for c in self.end_records(recorder)}
        self.assertEqual(by_session[session_a.pk]['reason'], 'kill')
        sibling = by_session[session_b.pk]
        self.assertEqual(sibling['outcome'], 'win')
        self.assertEqual(sibling['reason'], 'sibling_kill')
        self.assertEqual(sibling['npcs_remaining'], [])
        sibling_record = next(c for c in self.end_records(recorder)
                              if c['data']['session'] == session_b.pk)
        self.assertEqual(sibling_record['actor_id'], char_b.pk)

    def test_stale_maps_to_disengage_and_captures_npc_state(self):
        npc = make_npc(self.definition, self.room, hp=20)
        npc.vitality_current = 7
        npc.save(update_fields=['vitality_current'])
        session = make_session(self.char, [npc], self.room)
        session.last_tick_at = timezone.now() - timedelta(
            seconds=STALE_SESSION_SECS + 5)
        session.save(update_fields=['last_tick_at'])
        cmd, recorder, events = self.run_tick()
        ends = self.end_records(recorder)
        self.assertEqual(len(ends), 1)
        data = ends[0]['data']
        self.assertEqual(data['outcome'], 'disengage')
        self.assertEqual(data['reason'], 'stale')
        # npcs_remaining captured BEFORE the release reset them to full.
        self.assertEqual(data['npcs_remaining'],
                         [{'instance': npc.pk, 'vitality': [7, 20]}])
        npc.refresh_from_db()
        self.assertEqual(npc.vitality_current, 20)

    def test_self_heal_maps_to_disengage(self):
        npc = make_npc(self.definition, self.room, hp=20)
        npc.is_alive = False
        npc.save(update_fields=['is_alive'])
        session = make_session(self.char, [npc], self.room)
        cmd, recorder, events = self.run_tick()
        ends = self.end_records(recorder)
        self.assertEqual(len(ends), 1)
        data = ends[0]['data']
        self.assertEqual(data['outcome'], 'disengage')
        self.assertEqual(data['reason'], 'self_heal')
        self.assertEqual(data['npcs_remaining'], [])

    def test_empty_maps_to_disengage(self):
        npc = make_npc(self.definition, self.room, hp=20)
        session = CombatSession.objects.create(
            room=self.room, first_attacker='character',
            tick_counter=COMBAT_ROUND_TICKS - 1,
            last_tick_at=timezone.now())
        session.npcs.add(npc)   # living NPC, zero characters
        cmd, recorder, events = self.run_tick()
        ends = self.end_records(recorder)
        self.assertEqual(len(ends), 1)
        data = ends[0]['data']
        self.assertEqual(data['session'], session.pk)
        self.assertEqual(data['outcome'], 'disengage')
        self.assertEqual(data['reason'], 'empty')
        self.assertIsNone(ends[0]['actor_id'])

    def test_flee_maps_to_flee(self):
        refuge = self.zone.rooms.create(
            name='es Refuge', description='Long.', brief_description='Brief.',
            coord_x=0, coord_y=1)
        self.room.exit_north = refuge
        self.room.save(update_fields=['exit_north'])
        npc = make_npc(self.definition, self.room, hp=50)
        session = make_session(self.char, [npc], self.room)
        recorder = EmitRecorder()
        consumer = make_stub_consumer(self.char, [])
        consumer.last_direction = None
        # Force the contest: a natural 20 against a 1-PER NPC side.
        with mock.patch('apps.shyland.mc.mc_emit', new=recorder), \
             mock.patch('apps.shyland.consumers.random.randint',
                        return_value=20):
            asyncio.run(consumer.cmd_flee())
        kinds = recorder.kinds()
        self.assertEqual(kinds[0], 'combat_flee')
        flee = recorder.calls[0]
        self.assertEqual(flee['actor_id'], self.char.pk)
        self.assertEqual(flee['audience'], [])
        data = flee['data']
        self.assertEqual(data['session'], session.pk)
        self.assertEqual(data['die'], 20)
        self.assertEqual(data['total'], data['dex'] + 20)
        self.assertTrue(data['success'])
        self.assertEqual(data['destination'], refuge.pk)
        self.assertEqual(data['direction'], 'north')
        self.assertNotIn('blocked', data)
        end = next(c for c in recorder.calls if c['kind'] == 'combat_end')
        self.assertEqual(end['data']['outcome'], 'flee')
        self.assertEqual(end['data']['reason'], 'flee')
        # The surviving NPC's state was captured before the release reset.
        self.assertEqual(end['data']['npcs_remaining'],
                         [{'instance': npc.pk, 'vitality': [50, 50]}])

    def test_failed_flee_emits_the_contest_record(self):
        npc = make_npc(self.definition, self.room, hp=50)
        session = make_session(self.char, [npc], self.room)
        recorder = EmitRecorder()
        consumer = make_stub_consumer(self.char, [])
        consumer.last_direction = None
        # A natural 0-equivalent: the roll cannot beat the NPC side by
        # forcing DEX + 1 <= avg PER is fixture-dependent, so force the
        # contest the other way: die=1 against a raised NPC PER.
        self.definition.base_per = 500
        self.definition.save(update_fields=['base_per'])
        with mock.patch('apps.shyland.mc.mc_emit', new=recorder), \
             mock.patch('apps.shyland.consumers.random.randint',
                        return_value=1):
            asyncio.run(consumer.cmd_flee())
        # The consumer's send_output path emits v25.1 'out' records
        # through the same choke point — assert on the combat family.
        combat_kinds = [k for k in recorder.kinds() if k.startswith('combat_')]
        self.assertEqual(combat_kinds, ['combat_flee'])
        data = next(c for c in recorder.calls
                    if c['kind'] == 'combat_flee')['data']
        self.assertFalse(data['success'])
        self.assertEqual(data['die'], 1)
        self.assertNotIn('destination', data)
        self.assertNotIn('blocked', data)
        session.refresh_from_db()
        self.assertTrue(session.is_active)

    def test_flee_empty_maps_to_disengage(self):
        session = make_session(self.char, [], self.room)
        recorder = EmitRecorder()
        consumer = make_stub_consumer(self.char, [])
        consumer.last_direction = None
        with mock.patch('apps.shyland.mc.mc_emit', new=recorder):
            asyncio.run(consumer.cmd_flee())
        # send_status_refresh may emit non-combat records through the
        # same choke point — assert on the combat family.
        combat_kinds = [k for k in recorder.kinds() if k.startswith('combat_')]
        self.assertEqual(combat_kinds, ['combat_end'])
        data = next(c for c in recorder.calls
                    if c['kind'] == 'combat_end')['data']
        self.assertEqual(data['session'], session.pk)
        self.assertEqual(data['outcome'], 'disengage')
        self.assertEqual(data['reason'], 'flee_empty')
        self.assertEqual(data['npcs_remaining'], [])

    def test_death_maps_to_loss(self):
        Character.objects.filter(pk=self.char.pk).update(
            vitality_current=0, is_dying=True,
            dying_since=timezone.now() - timedelta(
                seconds=DYING_DURATION_SECS + 5))
        self.char.refresh_from_db()
        npc = make_npc(self.definition, self.room, hp=13)
        npc.vitality_current = 9
        npc.save(update_fields=['vitality_current'])
        session = make_session(self.char, [npc], self.room)
        cmd, recorder, events = self.run_tick()
        kinds = recorder.kinds()
        # The death-phase record, then the loss close.
        self.assertIn('combat_death', kinds)
        self.assertIn('combat_end', kinds)
        self.assertLess(kinds.index('combat_death'), kinds.index('combat_end'))
        death = next(c for c in recorder.calls if c['kind'] == 'combat_death')
        self.assertEqual(death['actor_id'], self.char.pk)
        data = death['data']
        self.assertEqual(data['phase'], 'death')
        self.assertEqual(data['character'], self.char.pk)
        # Field absence means not-applicable: the bare test world has no
        # travel nodes, so no home resolves and the key stays absent.
        self.assertNotIn('home_room', data)
        self.assertIsInstance(data['broken_items'], list)
        self.assertEqual(data['sessions_closed'], [session.pk])
        end = next(c for c in recorder.calls if c['kind'] == 'combat_end')
        self.assertEqual(end['data']['session'], session.pk)
        self.assertEqual(end['data']['outcome'], 'loss')
        self.assertEqual(end['data']['reason'], 'death')
        # The NPCs the faller was fighting were captured mid-fight,
        # before the release reset them.
        self.assertEqual(end['data']['npcs_remaining'],
                         [{'instance': npc.pk, 'vitality': [9, 13]}])
        # All emitted before the dying loop's sends.
        mc_indexes = [i for i, e in enumerate(events) if e[0] == 'mc']
        send_indexes = [i for i, e in enumerate(events) if e[0] != 'mc']
        self.assertLess(max(mc_indexes), min(send_indexes))


class FallTests(RoundHarness):
    """§6.8: the killing NPC blow — the action record carries
    target_fell, and the combat_death fall record follows it."""

    def setUp(self):
        self.zone, self.room = make_world('fl')
        self.char = make_character('fl', self.room)
        Character.objects.filter(pk=self.char.pk).update(
            vitality_current=1, vitality_max=100)
        self.definition = make_npc_definition('fl')
        self.definition.base_str = 500
        self.definition.save(update_fields=['base_str'])
        self.npc = make_npc(self.definition, self.room, hp=1000)
        self.session = make_session(self.char, [self.npc], self.room,
                                    tick_counter=COMBAT_ROUND_TICKS - 1)

    def test_fall_records_follow_the_killing_action(self):
        cmd, recorder, events = self.run_tick(
            resolve_side_effect=self.player_misses_npc_hits)
        kinds = recorder.kinds()
        # combat_round, player miss action, NPC action (the blow), fall.
        self.assertEqual(kinds[:4], ['combat_round', 'combat_action',
                                     'combat_action', 'combat_death'])
        blow = recorder.calls[2]
        self.assertIsNone(blow['actor_id'])
        self.assertTrue(blow['data']['target_fell'])
        self.assertEqual(blow['data']['target_vitality'][1], 0)
        # No effects field on the fall path — apply_npc_effects never ran.
        self.assertNotIn('effects', blow['data'])
        fall = recorder.calls[3]
        self.assertEqual(fall['data']['phase'], 'fall')
        self.assertEqual(fall['data']['round'], 1)
        self.assertEqual(fall['data']['character'], self.char.pk)
        self.assertEqual(fall['data']['killer'],
                         {'instance': self.npc.pk,
                          'definition': self.definition.pk,
                          'mk_tier': self.npc.mk_tier})
        # The fall record is session-scoped: the character is the actor.
        self.assertEqual(fall['actor_id'], self.char.pk)
        # The player's own miss action carried to_hit only.
        miss = recorder.calls[1]
        self.assertEqual(miss['actor_id'], self.char.pk)
        self.assertNotIn('damage', miss['data'])
        self.assertIn('to_hit', miss['data'])
