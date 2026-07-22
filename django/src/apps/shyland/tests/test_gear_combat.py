"""v22 Brief 5 (#100, #109, #110, #68's B5 half): gear combat wiring.

Effective stats (base + equipped gear) on every gameplay read, Option C
armor mitigation (TAV / (TAV + K)), the bar law (fill-fraction invariance
via one atomic rescale), proc factors / crit_chance / lifesteal /
electric_damage_bonus wiring with the hit-line parenthetical, the stats
display split, the proc-stat rename command, and #109's no-refill spend.
"""

import io

from asgiref.sync import sync_to_async
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland import combat_utils
from apps.shyland.combat_utils import (
    ARMOR_MITIGATION_K, ARMOR_SLOT_WEIGHTS, apply_armor_mitigation,
    bar_rescale_updates, effective_stats, gear_stat_bonus, resolve_hit,
    roll_gear_bonus_damage, summed_gear_stat, total_armor_value,
)
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    Character, CombatSession, ItemDefinition, ItemInstance, NpcDefinition,
    NpcInstance,
)

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world, outputs,
)


def make_gear_def(prefix, name, item_type='material', slot=None):
    return ItemDefinition.objects.create(
        name=name, slug=f'{prefix}-{name.lower().replace(" ", "-")}',
        item_type=item_type, genre_tag='fantasy',
        valid_slots=[slot] if slot else [],
        scaling_base=0.0, scaling_factor=0.0, base_value=1,
    )


def equip_gear(defn, char, slot, mk=1, primary=None, secondary=None,
               broken=False, durability=100.0):
    return ItemInstance.objects.create(
        definition=defn, owner=char, mk_tier=mk, rarity='common',
        durability_current=durability, is_broken=broken,
        is_identified=True, is_equipped=True, equipped_slot=slot,
        rolled_primary_stats=primary or [],
        rolled_secondary_stats=secondary or [],
    )


class MemItem:
    """In-memory stand-in: gear helpers read only the rolled-stat lists."""

    def __init__(self, primary=None, secondary=None):
        self.rolled_primary_stats = primary or []
        self.rolled_secondary_stats = secondary or []


# ----------------------------------------------------------------------
# Step 2 — the effective-stat function
# ----------------------------------------------------------------------

class EffectiveStatsTests(TestCase):

    def test_naked_equals_base(self):
        zone, room = make_world('efA')
        char = make_character('efA', room)
        eff = effective_stats(char)
        for key in ('str', 'dex', 'end', 'int', 'wis', 'per'):
            self.assertEqual(eff[key], getattr(char, f'stat_{key}'))
        self.assertEqual(gear_stat_bonus(char),
                         {k: 0 for k in ('str', 'dex', 'end', 'int', 'wis', 'per')})

    def test_equipped_gear_moves_the_stat_and_unequip_restores(self):
        zone, room = make_world('efB')
        char = make_character('efB', room)
        defn = make_gear_def('efB', 'Mighty Band', slot='RING')
        item = equip_gear(defn, char, 'RING',
                          primary=[{'stat': 'str', 'value': 3}])
        eff = effective_stats(char)
        self.assertEqual(eff['str'], char.stat_str + 3)
        for key in ('dex', 'end', 'int', 'wis', 'per'):
            self.assertEqual(eff[key], getattr(char, f'stat_{key}'))

        item.is_equipped = False
        item.save()
        self.assertEqual(effective_stats(char)['str'], char.stat_str)

    def test_gear_sum_rounds_to_nearest_per_stat(self):
        zone, room = make_world('efC')
        char = make_character('efC', room)
        defn = make_gear_def('efC', 'Half Charm', slot='RING')
        equip_gear(defn, char, 'RING', primary=[{'stat': 'str', 'value': 1.4}])
        equip_gear(defn, char, 'RING', primary=[{'stat': 'str', 'value': 1.4}])
        self.assertEqual(gear_stat_bonus(char)['str'], 3)  # 2.8 -> 3

    def test_secondary_entries_and_preloaded_list_count(self):
        zone, room = make_world('efD')
        char = make_character('efD', room)
        items = [MemItem(secondary=[{'stat': 'dex', 'value': 2}]),
                 MemItem(primary=[{'stat': 'dex', 'value': 1}])]
        self.assertEqual(gear_stat_bonus(char, items)['dex'], 3)

    def test_unsaved_character_has_no_gear(self):
        char = Character(stat_str=10)
        self.assertEqual(gear_stat_bonus(char)['str'], 0)


class CarryCapacityTests(TransactionTestCase):

    async def test_carry_reads_effective_str(self):
        def setup():
            zone, room = make_world('cc')
            char = make_character('cc', room)
            defn = make_gear_def('cc', 'Power Gauntlets', slot='HANDS')
            equip_gear(defn, char, 'HANDS',
                       primary=[{'stat': 'str', 'value': 3}])
            return char
        char = await sync_to_async(setup)()
        consumer = make_stub_consumer(char, [])
        current, max_carry = await consumer.get_carry_counts(char)
        self.assertEqual(max_carry, (char.stat_str + 3) * 10)
        _, max_capacity = await consumer.get_carry_capacity(char)
        self.assertEqual(max_capacity, (char.stat_str + 3) * 10)


# ----------------------------------------------------------------------
# Step 3 — armor mitigation
# ----------------------------------------------------------------------

class ArmorCurveTests(SimpleTestCase):

    def test_constants(self):
        self.assertEqual(ARMOR_MITIGATION_K, 48)
        self.assertEqual(sum(ARMOR_SLOT_WEIGHTS.values()), 13)
        self.assertEqual(ARMOR_SLOT_WEIGHTS['CHEST'], 3)

    def test_naked_unchanged(self):
        self.assertEqual(apply_armor_mitigation(28, 0), 28)

    def test_full_common_mk1_reduces_28_to_22(self):
        # TAV 13: 13/61 = 21.3% -> reduction round(5.967) = 6.
        self.assertEqual(apply_armor_mitigation(28, 13), 22)

    def test_tav_1_still_saves_1(self):
        # round(4 x 1/49) = 0 -> floored to 1.
        self.assertEqual(apply_armor_mitigation(4, 1), 3)

    def test_one_damage_always_lands(self):
        self.assertEqual(apply_armor_mitigation(1, 999), 1)


class TotalArmorValueTests(TestCase):

    FULL_SET = [('CHEST', 3), ('HEAD', 2), ('LEGS', 2), ('OFF_HAND', 2),
                ('SHOULDERS', 1), ('HANDS', 1), ('WAIST', 1), ('FEET', 1)]

    def _full_set(self, prefix, char):
        items = {}
        for slot, _ in self.FULL_SET:
            defn = make_gear_def(prefix, f'{prefix} {slot} piece',
                                 item_type='armor', slot=slot)
            items[slot] = equip_gear(defn, char, slot, mk=1)
        return items

    def test_full_common_mk1_set_is_13(self):
        zone, room = make_world('tvA')
        char = make_character('tvA', room)
        self._full_set('tvA', char)
        self.assertEqual(total_armor_value(char), 13)

    def test_broken_chestpiece_drops_out(self):
        zone, room = make_world('tvB')
        char = make_character('tvB', room)
        items = self._full_set('tvB', char)
        items['CHEST'].is_broken = True
        items['CHEST'].save()
        self.assertEqual(total_armor_value(char), 10)

    def test_zero_durability_drops_out_and_resist_joins_from_any_type(self):
        zone, room = make_world('tvC')
        char = make_character('tvC', room)
        helm_def = make_gear_def('tvC', 'Helm', item_type='armor', slot='HEAD')
        helm = equip_gear(helm_def, char, 'HEAD',
                          secondary=[{'stat': 'physical_resist', 'value': 4}])
        sword_def = make_gear_def('tvC', 'Sword', item_type='weapon',
                                  slot='MAIN_HAND')
        equip_gear(sword_def, char, 'MAIN_HAND',
                   secondary=[{'stat': 'physical_resist', 'value': 2}])
        # helm slot weight 2 + helm resist 4 + weapon resist 2 = 8 (weapon
        # slot carries no armor weight).
        self.assertEqual(total_armor_value(char), 8)
        helm.durability_current = 0.0
        helm.save()
        self.assertEqual(total_armor_value(char), 2)

    def test_naked_is_zero(self):
        zone, room = make_world('tvD')
        char = make_character('tvD', room)
        self.assertEqual(total_armor_value(char), 0)


# ----------------------------------------------------------------------
# Step 4 — the bar law (#110)
# ----------------------------------------------------------------------

class BarLawTests(TransactionTestCase):
    # Base character: END/STR/WIS 10, level 1 -> both maxima 135.

    def _char(self, prefix, vit=(54, 135), lon=(54, 135)):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        Character.objects.filter(pk=char.pk).update(
            vitality_current=vit[0], vitality_max=vit[1],
            longevity_current=lon[0], longevity_max=lon[1])
        return Character.objects.select_related('user').get(pk=char.pk)

    async def test_equip_end_gear_preserves_fill_fraction(self):
        char = await sync_to_async(self._char)('blA')  # 40% fill

        def make_item(char):
            defn = make_gear_def('blA', 'Stout Plate', item_type='armor',
                                 slot='CHEST')
            item = ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=1, rarity='common',
                is_identified=True,
                rolled_primary_stats=[{'stat': 'end', 'value': 2}])
            return item
        item = await sync_to_async(make_item)(char)
        consumer = make_stub_consumer(char, [])
        await consumer.equip_item(item, 'CHEST', char)

        def state():
            c = Character.objects.get(pk=char.pk)
            return (c.vitality_current, c.vitality_max,
                    c.longevity_current, c.longevity_max)
        vit_c, vit_m, lon_c, lon_m = await sync_to_async(state)()
        # END 12: vit max 155, lon max 151; 40% of each, nearest.
        self.assertEqual((vit_m, lon_m), (155, 151))
        self.assertEqual(vit_c, 62)   # round(54 x 155/135)
        self.assertEqual(lon_c, 60)   # round(54 x 151/135)

    async def test_unequip_at_full_stays_exactly_full(self):
        char = await sync_to_async(self._char)('blB')

        def make_equipped(char):
            defn = make_gear_def('blB', 'Stout Plate', item_type='armor',
                                 slot='CHEST')
            item = equip_gear(defn, char, 'CHEST',
                              primary=[{'stat': 'end', 'value': 2}])
            Character.objects.filter(pk=char.pk).update(
                vitality_current=155, vitality_max=155,
                longevity_current=151, longevity_max=151)
            return item
        item = await sync_to_async(make_equipped)(char)
        consumer = make_stub_consumer(char, [])
        await consumer.unequip_item(item)

        def state():
            c = Character.objects.get(pk=char.pk)
            return (c.vitality_current, c.vitality_max,
                    c.longevity_current, c.longevity_max)
        self.assertEqual(await sync_to_async(state)(), (135, 135, 135, 135))

    async def test_spend_end_no_refill(self):
        # Amendment 2 (#131) blocked in-combat spend, so the bar-law
        # spend case runs out of combat: bigger bar, same fraction,
        # no refill.
        char = await sync_to_async(self._char)('blC', vit=(67, 135), lon=(67, 135))

        def arm(char):
            Character.objects.filter(pk=char.pk).update(unspent_stat_points=1)
            return Character.objects.select_related('user').get(pk=char.pk)
        char = await sync_to_async(arm)(char)

        consumer = make_stub_consumer(char, [])
        await consumer.cmd_spend('1 end')

        def state():
            c = Character.objects.get(pk=char.pk)
            return (c.stat_end, c.vitality_current, c.vitality_max,
                    c.longevity_current, c.longevity_max)
        end, vit_c, vit_m, lon_c, lon_m = await sync_to_async(state)()
        self.assertEqual(end, 11)
        self.assertEqual((vit_m, lon_m), (145, 143))
        self.assertEqual(vit_c, 72)   # round(67 x 145/135) — NOT 145
        self.assertEqual(lon_c, 71)   # round(67 x 143/135) — NOT 143

    async def test_concurrent_stat_write_is_never_lost(self):
        # #110's shape: an effect-expiry stat write lands between the
        # consumer's read and its equip — the atomic F() update must see
        # the DB stat, and must not clobber it.
        char = await sync_to_async(self._char)('blD')

        def concurrent_and_item(char):
            # char was loaded (stat_end 10); the expiry write lands now.
            Character.objects.filter(pk=char.pk).update(stat_end=12)
            defn = make_gear_def('blD', 'Stout Plate', item_type='armor',
                                 slot='CHEST')
            return ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=1, rarity='common',
                is_identified=True,
                rolled_primary_stats=[{'stat': 'end', 'value': 2}])
        item = await sync_to_async(concurrent_and_item)(char)

        consumer = make_stub_consumer(char, [])   # stale char: stat_end 10
        await consumer.equip_item(item, 'CHEST', char)

        def state():
            c = Character.objects.get(pk=char.pk)
            return (c.stat_end, c.vitality_max)
        end, vit_m = await sync_to_async(state)()
        self.assertEqual(end, 12)                  # not clobbered back to 10
        self.assertEqual(vit_m, (12 + 2) * 10 + 30 + 5)   # 175, from DB truth

    async def test_dying_zero_stays_zero_and_floor_is_one(self):
        char = await sync_to_async(self._char)('blE', vit=(0, 135), lon=(1, 135))

        def make_item(char):
            defn = make_gear_def('blE', 'Stout Plate', item_type='armor',
                                 slot='CHEST')
            return ItemInstance.objects.create(
                definition=defn, owner=char, mk_tier=1, rarity='common',
                is_identified=True,
                rolled_primary_stats=[{'stat': 'end', 'value': 2}])
        item = await sync_to_async(make_item)(char)
        consumer = make_stub_consumer(char, [])
        await consumer.equip_item(item, 'CHEST', char)

        def state():
            c = Character.objects.get(pk=char.pk)
            return (c.vitality_current, c.longevity_current)
        vit_c, lon_c = await sync_to_async(state)()
        self.assertEqual(vit_c, 0)    # dying stays dying
        self.assertEqual(lon_c, 1)    # round(1 x 151/135) = 1, floored alive


# ----------------------------------------------------------------------
# Step 5 — procs, crit, lifesteal, electric
# ----------------------------------------------------------------------

class ProcRollTests(SimpleTestCase):

    def test_no_proc_stats_no_pool(self):
        items = [MemItem(primary=[{'stat': 'str', 'value': 3}])]
        self.assertEqual(roll_gear_bonus_damage(items), 0)

    def test_forced_success_rolls_one_to_ceil(self):
        items = [MemItem(secondary=[{'stat': 'bleed_factor', 'value': 3}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.random.return_value = 0.0
            rng.randint.return_value = 2
            self.assertEqual(roll_gear_bonus_damage(items), 2)
            rng.randint.assert_called_once_with(1, 3)

    def test_multiple_items_roll_independently_and_sum(self):
        items = [MemItem(secondary=[{'stat': 'bleed_factor', 'value': 3}]),
                 MemItem(secondary=[{'stat': 'poison_factor', 'value': 4}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.random.return_value = 0.0
            rng.randint.return_value = 2
            self.assertEqual(roll_gear_bonus_damage(items), 4)
            self.assertEqual(rng.randint.call_count, 2)
            rng.randint.assert_any_call(1, 3)
            rng.randint.assert_any_call(1, 4)

    def test_chance_is_v_times_005_capped_at_050(self):
        items = [MemItem(secondary=[{'stat': 'stun_factor', 'value': 20}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.randint.return_value = 1
            rng.random.return_value = 0.49   # under the 0.50 cap
            self.assertEqual(roll_gear_bonus_damage(items), 1)
            rng.random.return_value = 0.51   # over the cap — never fires
            self.assertEqual(roll_gear_bonus_damage(items), 0)

    def test_electric_is_flat_and_rollless(self):
        items = [MemItem(secondary=[{'stat': 'electric_damage_bonus', 'value': 5},
                                    {'stat': 'bleed_factor', 'value': 3}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.random.return_value = 1.0    # every proc roll fails
            self.assertEqual(roll_gear_bonus_damage(items), 5)

    def test_inert_stats_add_nothing(self):
        items = [MemItem(secondary=[
            {'stat': 'spell_damage_bonus', 'value': 9},
            {'stat': 'mana_regen', 'value': 9},
            {'stat': 'magic_resist', 'value': 9},
            {'stat': 'radiation_resist', 'value': 9},
        ])]
        self.assertEqual(roll_gear_bonus_damage(items), 0)
        self.assertEqual(summed_gear_stat(items, 'lifesteal'), 0)


class GearCritTests(SimpleTestCase):

    def test_crit_bonus_joins_capped_computation(self):
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.randint.return_value = 20
            rng.random.return_value = 0.10
            # Even DEX: base crit 0.05 — 0.10 misses the crit roll.
            self.assertEqual(resolve_hit(10, 10), 'hit')
            # +10 points of gear crit_chance -> 0.15 — now it crits.
            self.assertEqual(resolve_hit(10, 10, crit_bonus=0.10), 'critical')
            # The cap holds: an absurd bonus still tops out at CRIT_CAP.
            rng.random.return_value = 0.30
            self.assertEqual(resolve_hit(10, 10, crit_bonus=5.0), 'hit')


def run_engine_round():
    """CritProseTests-style engine harness with stubbed delivery.
    Returns (cmd, player_msgs, room_msgs)."""
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
    return cmd, player_msgs, room_msgs


def make_combat_world(prefix, npc_vitality=1000, npc_str=1):
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    Character.objects.filter(pk=char.pk).update(
        vitality_current=100, vitality_max=500)
    definition = NpcDefinition.objects.create(
        name=f'{prefix} beetle', slug=f'{prefix}-beetle',
        description='x', genre_tag='fantasy',
        base_vitality=npc_vitality, base_str=npc_str, base_dex=1,
        base_end=1, base_int=1, base_wis=1, base_per=1,
    )
    npc = NpcInstance.objects.create(
        definition=definition, current_room=room, spawn_room=room,
        vitality_current=npc_vitality, vitality_max=npc_vitality,
    )
    from apps.shyland.models import COMBAT_ROUND_TICKS
    session = CombatSession.objects.create(
        room=room, last_tick_at=timezone.now(),
        tick_counter=COMBAT_ROUND_TICKS - 1,
    )
    session.characters.add(char)
    session.npcs.add(npc)
    return char, npc


class EngineGearTests(TransactionTestCase):
    """The wiring inside the round: parenthetical, lifesteal, NPC purity."""

    async def test_zero_pool_line_byte_identical_no_parenthetical(self):
        char, npc = await sync_to_async(make_combat_world)('egA')
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='hit'):
            await cmd.process_combat(1)
        out_hits = [t for _, t, c in player_msgs if c == 'combat-hit-out']
        self.assertTrue(out_hits)
        self.assertRegex(out_hits[0], r'for \d+ damage\.')
        self.assertNotIn('(+', out_hits[0])

    async def test_electric_parenthetical_and_npc_lines_stay_pure(self):
        def setup():
            char, npc = make_combat_world('egB')
            defn = make_gear_def('egB', 'Live Wire')
            equip_gear(defn, char, 'WAIST', secondary=[
                {'stat': 'electric_damage_bonus', 'value': 5}])
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='hit'):
            await cmd.process_combat(1)

        out_hits = [t for _, t, c in player_msgs if c == 'combat-hit-out']
        self.assertTrue(out_hits)
        self.assertRegex(out_hits[0], r'for \d+ \(\+5\) damage\.')

        # NPC damage to players never gains procs — no parenthetical on
        # the incoming line even with a gear-laden defender.
        in_hits = [t for _, t, c in player_msgs if c == 'combat-hit-in']
        self.assertTrue(in_hits)
        self.assertNotIn('(+', in_hits[0])

        # Total dealt = base + bonus: the NPC lost base+5.
        def npc_vit():
            return NpcInstance.objects.get(pk=npc.pk).vitality_current
        import re
        base = int(re.search(r'for (\d+) \(\+5\) damage', out_hits[0]).group(1))
        self.assertEqual(await sync_to_async(npc_vit)(), 1000 - base - 5)

    async def test_graze_never_rolls_the_pool(self):
        def setup():
            char, npc = make_combat_world('egC')
            defn = make_gear_def('egC', 'Live Wire')
            equip_gear(defn, char, 'WAIST', secondary=[
                {'stat': 'electric_damage_bonus', 'value': 5}])
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        return_value='graze'):
            await cmd.process_combat(1)
        for _, text, _ in player_msgs:
            self.assertNotIn('(+', text)

    async def test_lifesteal_heals_flat_and_silent(self):
        def setup():
            char, npc = make_combat_world('egD')
            defn = make_gear_def('egD', 'Leech Fang')
            equip_gear(defn, char, 'WAIST', secondary=[
                {'stat': 'lifesteal', 'value': 5}])
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()

        def player_hits_npc_misses(attacker_dex, target_dodge, crit_bonus=None):
            # The player path passes crit_bonus; the NPC path does not.
            return 'hit' if crit_bonus is not None else 'miss'
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        side_effect=player_hits_npc_misses):
            await cmd.process_combat(1)

        def vit():
            return Character.objects.get(pk=char.pk).vitality_current
        self.assertEqual(await sync_to_async(vit)(), 105)   # 100 + 5, one hit
        for _, text, _ in player_msgs:
            self.assertNotIn('lifesteal', text.lower())
            self.assertNotIn('drain', text.lower())

    async def test_lifesteal_clamps_at_vitality_max(self):
        def setup():
            char, npc = make_combat_world('egE')
            Character.objects.filter(pk=char.pk).update(
                vitality_current=500, vitality_max=500)
            defn = make_gear_def('egE', 'Leech Fang')
            equip_gear(defn, char, 'WAIST', secondary=[
                {'stat': 'lifesteal', 'value': 5}])
            return char, npc
        char, npc = await sync_to_async(setup)()
        cmd, player_msgs, _ = run_engine_round()

        def player_hits_npc_misses(attacker_dex, target_dodge, crit_bonus=None):
            return 'hit' if crit_bonus is not None else 'miss'
        with mock.patch('apps.shyland.combat_utils.resolve_hit',
                        side_effect=player_hits_npc_misses):
            await cmd.process_combat(1)

        def vit():
            return Character.objects.get(pk=char.pk).vitality_current
        self.assertEqual(await sync_to_async(vit)(), 500)


class RenameCommandTests(TransactionTestCase):

    def test_rename_is_value_preserving_and_idempotent(self):
        zone, room = make_world('rn')
        char = make_character('rn', room)
        defn = make_item_def('rn', 'Old Blade')
        item = make_owned_item(defn, char)
        ItemInstance.objects.filter(pk=item.pk).update(
            rolled_primary_stats=[{'stat': 'poison_chance', 'value': 1}],
            rolled_secondary_stats=[{'stat': 'bleed_chance', 'value': 3},
                                    {'stat': 'stun_chance', 'value': 2},
                                    {'stat': 'crit_chance', 'value': 4},
                                    {'stat': 'lifesteal', 'value': 5}])
        out = io.StringIO()
        call_command('rename_proc_stats', stdout=out)
        self.assertIn('3 entries renamed on 1 item(s)', out.getvalue())

        item.refresh_from_db()
        self.assertEqual(item.rolled_primary_stats,
                         [{'stat': 'poison_factor', 'value': 1}])
        self.assertEqual(item.rolled_secondary_stats,
                         [{'stat': 'bleed_factor', 'value': 3},
                          {'stat': 'stun_factor', 'value': 2},
                          {'stat': 'crit_chance', 'value': 4},
                          {'stat': 'lifesteal', 'value': 5}])

        out2 = io.StringIO()
        call_command('rename_proc_stats', stdout=out2)
        self.assertIn('0 entries renamed on 0 item(s)', out2.getvalue())


class SeedUsesNewNamesTests(SimpleTestCase):

    def test_seed_world_has_no_old_proc_names(self):
        import apps.shyland.management.commands.seed_world as seed_module
        source = open(seed_module.__file__).read()
        for old in ('bleed_chance', 'stun_chance', 'poison_chance'):
            self.assertNotIn(old, source)
        self.assertIn('bleed_factor', source)


# ----------------------------------------------------------------------
# Steps 6 and 7 — stats display, no-refill spend output
# ----------------------------------------------------------------------

class StatsDisplayTests(TransactionTestCase):

    def _stat_lines(self, sent):
        for msg in sent:
            if msg.get('type') == 'output' and 'lines' in msg:
                return [line.get('v', '') for line in msg['lines'] if line]
        return []

    async def test_no_gear_no_parenthetical(self):
        def setup():
            zone, room = make_world('sdA')
            return make_character('sdA', room)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()
        lines = self._stat_lines(sent)
        self.assertIn('  Strength     (STR): 10', lines)
        for line in lines:
            self.assertNotIn('(+', line)

    async def test_gear_parenthetical_appears_and_goes(self):
        def setup():
            zone, room = make_world('sdB')
            char = make_character('sdB', room)
            defn = make_gear_def('sdB', 'Mighty Band', slot='RING')
            item = equip_gear(defn, char, 'RING',
                              primary=[{'stat': 'str', 'value': 3}])
            return char, item
        char, item = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_stats()
        lines = self._stat_lines(sent)
        self.assertIn('  Strength     (STR): 10 (+3)', lines)
        self.assertIn('  Dexterity    (DEX): 10', lines)

        def unequip(item):
            item.is_equipped = False
            item.save()
        await sync_to_async(unequip)(item)
        sent.clear()
        await consumer.cmd_stats()
        lines = self._stat_lines(sent)
        self.assertIn('  Strength     (STR): 10', lines)
        for line in lines:
            self.assertNotIn('(+', line)


class SpendNoRefillOutputTests(TransactionTestCase):

    async def test_spend_output_is_exactly_the_two_sentences(self):
        def setup():
            zone, room = make_world('nr')
            char = make_character('nr', room)
            Character.objects.filter(pk=char.pk).update(
                unspent_stat_points=1, vitality_current=67, vitality_max=135,
                longevity_current=67, longevity_max=135)
            return Character.objects.select_related('user').get(pk=char.pk)
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_spend('1 end')
        texts = [m['text'] for m in outputs(sent)]
        self.assertEqual(texts, [
            'You spend 1 point on Endurance.',
            'Endurance is now 11. No stat points remaining.',
        ])
