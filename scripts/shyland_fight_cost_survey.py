#!/usr/bin/env python3
"""Shyland V24.1 Brief 1 (#180) — post-gear-wiring fight-cost survey harness.

Runs INSIDE the django container against the seeded dev database:

    docker cp scripts/shyland_fight_cost_survey.py game-mvc-django:/tmp/
    docker exec -w /app game-mvc-django python /tmp/shyland_fight_cost_survey.py \
        --out /tmp/survey_out --commit <git-hash>
    docker cp game-mvc-django:/tmp/survey_out ./survey_out

The harness drives the SHIPPED combat code — it imports and calls the real
functions from apps.shyland.combat_utils, item_utils, and effect_utils, and
replicates the tick engine's per-round CALL SEQUENCE (not its formulas) from
run_tick_engine.py execute_actions().  Replicated-sequence citations
(run_tick_engine.py at the V24.1 branch tip):

  - one equipped-set load per round feeding effective stats / TAV / gear
    crit / lifesteal .......................................... lines 410-421
  - round ordering: first round by session first_attacker
    ('npc' for aggro engagement, consumers.py:624; 'character' for a
    player-initiated attack, consumers.py:2399); later rounds by
    roll_initiative(effective DEX, PER) vs the mean of per-NPC
    initiative rolls, player acts first on ties ............... lines 359-383
  - player attack: resolve_hit(eff dex, npc dex, crit_bonus=gear crit),
    weapon base damage uniform(midpoint-spread, midpoint+spread),
    stat bonus = effective STR (melee), durability modifier via
    get_durability_penalty, calculate_damage, int-truncate min 1,
    landed (hit/critical) rolls roll_gear_bonus_damage, lifesteal
    heals flat clamped at vitality_max ........................ lines 444-502
  - NPC attack: resolve_hit(npc dex, eff dex), base damage
    uniform(0.8*STR, 1.2*STR), calculate_damage(base, 0, 1.0, 1.0),
    int-truncate min 1, then apply_armor_mitigation(dmg, TAV) .. lines 614-643
  - a mid-round kill removes the NPC before its queued action
    resolves (live_npcs pruning) .............................. lines 438-439,
                                                                608-610
  - NPC actions are generated only for NPCs alive at round start . lines 331-342

Faithful optimizations (deterministic values hoisted, never reformulated):
get_npc_stats() contest stats are computed once per member (definition and
mk_tier are fixed; only the 'vitality' key varies and the simulator tracks
HP itself), and the equipped-set derivations (effective stats, TAV, gear
crit, lifesteal, bar maxima) are precomputed once per distinct loadout
variant — gear cannot change mid-fight in the simulated scenarios, and an
Uncommon weapon has exactly four possible secondary-slot variants.

NO PERSISTENT DB WRITES: every ORM object the simulator uses (Character,
ItemInstance, NpcInstance) is constructed in memory and never .save()d; the
database is only read (NpcDefinition, RoomSpawn, ItemDefinition,
VendorEntry, LootTableEntry, EffectDefinition).

Encounter model (#89, reused unchanged): all aggro members engage from
round 1; the player kills in ascending-HP order (adds first), retargeting
instantly (focus change is a free action, consumers.py:2384); passive NPCs
are fought one at a time (solo rows).  Mid-fight gated-add respawn
(respawn_minutes 1-10 at the tip) is OUTSIDE this model, exactly as it was
outside #89's; fights whose mean duration exceeds the shortest member
respawn timer are flagged in the report.
"""

import argparse
import csv
import json
import math
import os
import random
import statistics
from collections import defaultdict

import sys

import django

sys.path.insert(0, '/app')      # the container's Django source root
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_mvc.settings.production')
django.setup()

from apps.shyland.combat_utils import (          # noqa: E402  (real functions)
    NPC_CONTEST_BASE, NPC_CONTEST_STEP, NPC_TIER_OFFSET,
    acuity_damage_modifier, apply_armor_mitigation, calculate_damage,
    effective_stats, get_npc_stats, recalculate_bars, resolve_hit,
    roll_gear_bonus_damage, roll_initiative, summed_gear_stat,
    total_armor_value,
)
from apps.shyland.effect_utils import percent_heal_amount   # noqa: E402
from apps.shyland.item_utils import (                        # noqa: E402
    RARITY_SPREAD, get_durability_penalty,
)
from apps.shyland.models import (                            # noqa: E402
    Character, EffectDefinition, ItemDefinition, ItemInstance,
    LootTableEntry, NpcDefinition, NpcInstance, RoomSpawn, VendorEntry,
)

# ---------------------------------------------------------------- constants
RNG_SEED = 180                     # the founding ticket number
N_TRIALS = 10_000                  # per (encounter x level x scenario)
MAX_ROUNDS = 100_000               # backstop; unwinnable trials are pre-detected
DRAUGHT_PRICE_CP = 15              # seeded vendor price, all draught vendors
STACK_BOUND = 20                   # #89's ruled carried-stack feasibility bound
SPEND_DOWN = 0.75                  # #89: player heals above 25% of own pool
REFERENCE_LEVELS = (5, 10)         # #89 comparability columns
ARMOR_SLOTS = ('CHEST', 'HEAD', 'LEGS', 'OFF_HAND',
               'SHOULDERS', 'HANDS', 'WAIST', 'FEET')
# v21 B3 (#101) blessed at-level hit targets, from the get_npc_stats
# docstring at the tip: 55% normal / 45% elite / 45% boss.  (#89 quoted the
# pre-retune 55/40/25 targets; those no longer exist in the code.)
BLESSED_TARGET = {'normal': 0.55, 'elite': 0.45, 'boss': 0.45}

# ------------------------------------------------- expected-roll arithmetic


def expected_rolled_int(midpoint, rarity):
    """Exact E[round(uniform(midpoint*lo, midpoint*hi))] — the distribution
    mean of the integer stat value item_utils._roll_stat() stores.  A
    uniform draw hits an exact .5 boundary with probability zero, so
    banker's rounding at .5 contributes no mass."""
    lo_f, hi_f = RARITY_SPREAD[rarity]
    a, b = midpoint * lo_f, midpoint * hi_f
    if b <= a:
        return float(round(a))
    total = 0.0
    k = math.floor(a + 0.5)              # round(a) neighborhood start
    if k + 0.5 < a:
        k += 1
    while k - 0.5 < b:
        seg_lo = max(a, k - 0.5)
        seg_hi = min(b, k + 0.5)
        if seg_lo < seg_hi:
            total += k * (seg_hi - seg_lo) / (b - a)
        k += 1
    return total


def expected_midpoint(definition, mk_tier, rarity):
    """E[damage_midpoint] for a weapon instance: raw midpoint times the mean
    of the rarity spread (item_utils.generate_item_instance)."""
    raw = definition.scaling_base + definition.scaling_factor * mk_tier
    lo_f, hi_f = RARITY_SPREAD[rarity]
    return raw * (lo_f + hi_f) / 2.0

# ----------------------------------------------------------- loadout build


def build_expected_item(definition, mk_tier, rarity, slot,
                        include_primary=True, secondary_entry=None):
    """An in-memory ItemInstance at expected instance stats (never saved)."""
    prim = []
    if include_primary:
        for s in definition.primary_stats:
            mid = s['base'] + s['factor'] * mk_tier
            prim.append({'stat': s['stat'],
                         'value': expected_rolled_int(mid, rarity)})
    sec = [dict(secondary_entry)] if secondary_entry else []
    dmg_mid = dmg_spread = None
    if definition.item_type == 'weapon':
        dmg_mid = expected_midpoint(definition, mk_tier, rarity)
        dmg_spread = definition.damage_spread
    return ItemInstance(
        definition=definition, mk_tier=mk_tier, rarity=rarity,
        rolled_primary_stats=prim, rolled_secondary_stats=sec,
        damage_midpoint=dmg_mid, damage_spread=dmg_spread,
        durability_current=100.0, is_broken=False,
        is_equipped=True, equipped_slot=slot,
    )


def attainable_armor_definitions():
    """Armor definitions realistically attainable in the Mk 1 band:
    vendor-stocked anywhere (active entry, Mk 1) or carrying an effective
    per-kill drop chance >= 0.10 in a loot table whose Mk band covers 1.
    Grouped (guaranteed_group) entries use their weight share of the group
    as the effective chance — the group drops exactly one member per kill
    (item_utils.generate_loot_from_table)."""
    ok = {}
    for v in VendorEntry.objects.filter(
            is_active=True, mk_tier=1,
            item_definition__item_type='armor').select_related(
            'item_definition', 'npc_definition'):
        ok.setdefault(v.item_definition.slug, []).append(
            f'vendor:{v.npc_definition.slug}@{v.price}cp')
    entries = list(LootTableEntry.objects.filter(
        item_definition__item_type='armor',
        mk_tier_min__lte=1, mk_tier_max__gte=1).select_related(
        'item_definition', 'loot_table'))
    group_totals = defaultdict(float)
    for e in entries:
        if e.guaranteed_group:
            group_totals[(e.loot_table_id, e.guaranteed_group)] += e.drop_chance
    for e in entries:
        if e.guaranteed_group:
            chance = e.drop_chance / group_totals[(e.loot_table_id,
                                                   e.guaranteed_group)]
        else:
            chance = e.drop_chance
        if chance >= 0.10:
            ok.setdefault(e.item_definition.slug, []).append(
                f'drop:{e.loot_table.slug}@{chance:.3f}')
    return ok


def build_headline_armor(two_handed_weapon):
    """Per Option-C armor slot, the best realistically attainable Mk 1
    piece at Common expected stats.  TAV contribution per slot is identical
    across candidates (slot weight x Mk; Common rolls no secondary
    physical_resist), so 'best' resolves on the expected primary-stat sum
    (END on every seeded piece), the stat the gear wiring feeds into
    vitality_max.  OFF_HAND is skipped when the weapon is two-handed —
    equipping it would displace the weapon (consumers.py:1231-1236)."""
    attain = attainable_armor_definitions()
    defs = {d.slug: d for d in ItemDefinition.objects.filter(item_type='armor')}
    chosen, table = [], []
    for slot in ARMOR_SLOTS:
        if slot == 'OFF_HAND' and two_handed_weapon:
            table.append({'slot': slot, 'piece': None,
                          'reason': 'two-handed weapon occupies both hands'})
            continue
        best, best_score, best_src = None, -1.0, None
        for slug, sources in sorted(attain.items()):
            d = defs[slug]
            if slot not in d.valid_slots:
                continue
            score = sum(expected_rolled_int(s['base'] + s['factor'] * 1,
                                            'common')
                        for s in d.primary_stats)
            if score > best_score:
                best, best_score, best_src = d, score, sources
        if best is None:
            table.append({'slot': slot, 'piece': None,
                          'reason': 'no attainable Mk 1 piece'})
            continue
        chosen.append(build_expected_item(best, 1, 'common', slot))
        table.append({'slot': slot, 'piece': best.slug,
                      'expected_primary': {
                          s['stat']: round(expected_rolled_int(
                              s['base'] + s['factor'] * 1, 'common'), 4)
                          for s in best.primary_stats},
                      'sources': best_src})
    return chosen, table


def weapon_secondary_pool(definition, mk_tier, rarity):
    """The weapon's secondary-stat pool with each entry at its exact
    expected rolled integer value.  An Uncommon instance rolls exactly one
    of these (item_utils.RARITY_SECONDARY_SLOTS); the simulator samples the
    slot uniformly per trial — the Monte Carlo marginalization of 'expected
    instance stats' over the slot choice."""
    pool = []
    for s in definition.secondary_stat_pool:
        mid = s['base'] + s['factor'] * mk_tier
        pool.append({'stat': s['stat'],
                     'value': expected_rolled_int(mid, rarity)})
    return pool

# ------------------------------------------------------- reference player


def reference_player(level):
    """#89 §1.2 verbatim: Blade, creation primaries STR/DEX 18 others 8,
    +5 points/level split evenly into STR/DEX with STR taking the odd
    point; Acuity in-band (1.0); END stays 8."""
    points = 5 * (level - 1)
    add_str = points // 2 + points % 2
    add_dex = points // 2
    return Character(
        level=level,
        stat_str=18 + add_str, stat_dex=18 + add_dex,
        stat_end=8, stat_int=8, stat_wis=8, stat_per=8,
        acuity_current=1.0, acuity_baseline=1.0,
        acuity_band_low=0.85, acuity_band_high=1.15,
    )

# ------------------------------------------------------ encounter builders


def npc_contest_stats(definition):
    """One real get_npc_stats() call on a fresh in-memory Mk 1 instance;
    the contest keys are deterministic per (definition, mk_tier)."""
    inst = NpcInstance(definition=definition, mk_tier=1,
                       vitality_current=definition.base_vitality,
                       vitality_max=definition.base_vitality)
    return get_npc_stats(inst)


def build_encounters():
    """The survey population: every attackable combat NPC solo, every
    boss + gated-adds group, every multi-aggro co-spawn room composition
    (deduplicated across rooms, rooms recorded)."""
    defs = list(NpcDefinition.objects.filter(attackable=True))
    by_slug = {d.slug: d for d in defs}
    encounters = []
    for d in sorted(defs, key=lambda x: x.slug):
        encounters.append({
            'id': f'solo:{d.slug}', 'kind': 'solo',
            'tier': d.combat_tier, 'members': [d.slug],
            'at_level': int(d.scaling_factor), 'rooms': [],
        })

    spawns = list(RoomSpawn.objects.filter(
        is_active=True, npc_definition__attackable=True).select_related(
        'room', 'npc_definition', 'requires_living_npc'))
    rooms = defaultdict(list)
    for s in spawns:
        rooms[s.room_id].append(s)

    seen_groups = {}
    for room_spawns in rooms.values():
        room_name = room_spawns[0].room.name
        gated = [s for s in room_spawns if s.requires_living_npc_id]
        if gated:
            boss_slugs = {s.requires_living_npc.slug for s in gated}
            for boss_slug in sorted(boss_slugs):
                boss = by_slug[boss_slug]
                members = [boss_slug]
                for s in gated:
                    if s.requires_living_npc.slug == boss_slug:
                        members += [s.npc_definition.slug] * s.count
                key = ('boss', tuple(sorted(members)))
                if key in seen_groups:
                    seen_groups[key]['rooms'].append(room_name)
                    continue
                enc = {'id': f'boss:{boss_slug}', 'kind': 'boss-group',
                       'tier': 'boss', 'members': members,
                       'at_level': int(boss.scaling_factor),
                       'rooms': [room_name]}
                seen_groups[key] = enc
                encounters.append(enc)
            continue
        aggro = []
        for s in room_spawns:
            if s.npc_definition.is_aggressive:
                aggro += [s.npc_definition.slug] * s.count
        if len(aggro) < 2:
            continue
        key = ('room', tuple(sorted(aggro)))
        if key in seen_groups:
            seen_groups[key]['rooms'].append(room_name)
            continue
        level = max(int(by_slug[m].scaling_factor) for m in aggro)
        label = '+'.join(sorted(aggro))
        enc = {'id': f'room:{label}', 'kind': 'multi-aggro',
               'tier': 'multi-aggro', 'members': sorted(aggro),
               'at_level': level, 'rooms': [room_name]}
        seen_groups[key] = enc
        encounters.append(enc)
    return encounters, by_slug


def reconciliation():
    """§4.1: account for every NpcDefinition at the tip, #89 §1.4 style."""
    out = {'attackable_combat': [], 'non_attackable': [],
           'attackable_placeholder': []}
    for d in NpcDefinition.objects.all().order_by('slug'):
        if not d.attackable:
            out['non_attackable'].append(d.slug)
        elif d.base_vitality == 999 and d.base_str == 1:
            out['attackable_placeholder'].append(d.slug)
        else:
            out['attackable_combat'].append(d.slug)
    out['counts'] = {k: len(v) for k, v in out.items() if isinstance(v, list)}
    out['total'] = NpcDefinition.objects.count()
    return out

# ------------------------------------------------------------- the simulator


def loadout_configs(player_level, weapon_def, weapon_rarity, armor_items,
                    sample_secondary, statless_weapon=False):
    """Precompute the distinct loadout variants for one scenario cell.

    An Uncommon weapon rolls exactly one secondary from a fixed pool, so
    per-trial sampling over instances collapses to a uniform choice over
    these variants.  Each config carries the tick engine's per-round
    derivations (run_tick_engine.py:410-421), computed by the real shipped
    functions."""
    if statless_weapon:
        weapons = [build_expected_item(weapon_def, 1, weapon_rarity,
                                       'MAIN_HAND', include_primary=False)]
    elif sample_secondary:
        pool = weapon_secondary_pool(weapon_def, 1, weapon_rarity)
        weapons = [build_expected_item(weapon_def, 1, weapon_rarity,
                                       'MAIN_HAND', secondary_entry=e)
                   for e in pool]
    else:
        weapons = [build_expected_item(weapon_def, 1, weapon_rarity,
                                       'MAIN_HAND')]
    configs = []
    for weapon in weapons:
        equipped = [weapon] + armor_items
        player = reference_player(player_level)
        eff = effective_stats(player, equipped)
        vit_max, _ = recalculate_bars(player, equipped)
        configs.append({
            'equipped': equipped,
            'eff': eff,
            'vit_max': vit_max,
            'tav': total_armor_value(player, equipped),
            'crit_bonus': summed_gear_stat(equipped, 'crit_chance') * 0.01,
            'lifesteal': int(round(summed_gear_stat(equipped, 'lifesteal'))),
            'acuity_mod': acuity_damage_modifier(player),
            'dur_mod': 1.0 - get_durability_penalty(weapon),
            'mid': weapon.damage_midpoint,
            'spread': weapon.damage_spread or 0,
        })
    return configs


def run_trials(encounter, by_slug, configs, n_trials):
    """Monte Carlo core for one (encounter x level x scenario) cell.

    HP loss is NET (lifesteal included, per the brief); death-unhealed uses
    the RUNNING loss maximum — the player dies the moment cumulative
    unhealed loss reaches the pool, even if later lifesteal would have
    pulled the final net loss back under it."""
    members = [by_slug[m] for m in encounter['members']]
    # Kill order: ascending authored HP (adds first), ties by slug.
    members = sorted(members, key=lambda d: (d.base_vitality, d.slug))
    stats = [npc_contest_stats(d) for d in members]
    hp0 = [d.base_vitality for d in members]
    any_aggro = any(d.is_aggressive for d in members)
    n_members = len(members)
    max_npc_dex = max(s['dex'] for s in stats)

    losses, peaks, rounds_list = [], [], []
    hits = attacks = 0
    total_damage_dealt = 0.0
    total_rounds = 0
    deaths = 0
    unwinnable = 0

    for _ in range(n_trials):
        cfg = configs[0] if len(configs) == 1 else random.choice(configs)
        eff = cfg['eff']
        # Damage-path pre-check (d20 saturation): the hardest member must
        # be reachable at least by graze or the trial can never clear
        # (success needs defense - attacker_dex <= 10; graze extends the
        # reachable band by GRAZE_WINDOW = 3).
        if max_npc_dex - eff['dex'] > 13:
            unwinnable += 1
            continue
        equipped = cfg['equipped']
        vit_max = cfg['vit_max']
        char_tav = cfg['tav']
        gear_crit_bonus = cfg['crit_bonus']
        gear_lifesteal = cfg['lifesteal']
        acuity_mod = cfg['acuity_mod']
        dur_mod = cfg['dur_mod']
        mid = cfg['mid']
        spread = cfg['spread']

        hp = list(hp0)
        alive = [True] * n_members
        n_alive = n_members
        target = 0                       # ascending-HP focus pointer
        player_hp = float(vit_max)
        min_hp = player_hp
        rnd = 0
        capped = False
        while n_alive:
            rnd += 1
            if rnd > MAX_ROUNDS:         # backstop; unreachable by design
                capped = True
                break
            living_idx = [i for i in range(n_members) if alive[i]]
            if rnd == 1:
                player_first = not any_aggro   # first_attacker semantics
            else:
                char_init = roll_initiative(eff['dex'], eff['per'])
                avg_npc = (sum(roll_initiative(stats[i]['dex'],
                                               stats[i]['per'])
                               for i in living_idx) / len(living_idx))
                player_first = char_init >= avg_npc

            def player_attack():
                nonlocal hits, attacks, total_damage_dealt, target
                nonlocal n_alive, player_hp
                if not n_alive:
                    return
                while not alive[target]:
                    target += 1
                attacks += 1
                hit_result = resolve_hit(eff['dex'], stats[target]['dex'],
                                         crit_bonus=gear_crit_bonus)
                if hit_result == 'miss':
                    return
                base = random.uniform(mid - spread, mid + spread)
                dmg = calculate_damage(base, eff['str'], acuity_mod,
                                       dur_mod, hit_result,
                                       is_focus_target=True)
                dmg_int = max(1, int(dmg))
                landed = hit_result in ('hit', 'critical')
                if landed:
                    hits += 1
                gear_bonus = roll_gear_bonus_damage(equipped) if landed else 0
                total_damage_dealt += dmg_int + gear_bonus
                hp[target] -= dmg_int + gear_bonus
                if landed and gear_lifesteal > 0:
                    player_hp = min(float(vit_max),
                                    player_hp + gear_lifesteal)
                if hp[target] <= 0:
                    alive[target] = False
                    n_alive -= 1

            def npc_attack(i):
                nonlocal player_hp, min_hp
                hit_result = resolve_hit(stats[i]['dex'], eff['dex'])
                if hit_result == 'miss':
                    return
                base = random.uniform(stats[i]['str'] * 0.8,
                                      stats[i]['str'] * 1.2)
                dmg = calculate_damage(base, 0, 1.0, 1.0, hit_result,
                                       is_focus_target=True)
                dmg_int = max(1, int(dmg))
                dmg_int = apply_armor_mitigation(dmg_int, char_tav)
                player_hp -= dmg_int
                min_hp = min(min_hp, player_hp)

            if player_first:
                player_attack()
                for i in living_idx:
                    if alive[i]:         # mid-round kill skips the action
                        npc_attack(i)
            else:
                for i in living_idx:
                    npc_attack(i)
                player_attack()

        if capped:
            unwinnable += 1
            continue
        total_rounds += rnd
        losses.append(vit_max - player_hp)
        peaks.append(vit_max - min_hp)
        rounds_list.append(rnd)
        if min_hp <= 0:
            deaths += 1

    n_ok = len(losses)
    result = {
        'n_trials': n_trials, 'n_resolved': n_ok,
        'unwinnable_fraction': unwinnable / n_trials,
        'vitality_max': configs[0]['vit_max'],
    }
    if n_ok:
        losses_s = sorted(losses)

        def pct(p):
            return losses_s[min(n_ok - 1, int(p * n_ok))]
        vit_max = configs[0]['vit_max']
        heal = percent_heal_amount(0.15 + 0.05 * 1, vit_max)
        mean_loss = statistics.fmean(losses)
        result.update({
            'draught_heal': heal,
            'hp_loss_mean': mean_loss,
            'hp_loss_std': statistics.pstdev(losses),
            'hp_loss_p10': pct(0.10), 'hp_loss_p90': pct(0.90),
            'hp_loss_frac_mean': mean_loss / vit_max,
            'rounds_mean': statistics.fmean(rounds_list),
            'rounds_std': statistics.pstdev(rounds_list),
            'p_death_unhealed': deaths / n_ok,
            'draughts_per_fight': mean_loss / heal,
            'draught_cost_cp': (mean_loss / heal) * DRAUGHT_PRICE_CP,
            'potions_to_win': math.ceil(max(
                0.0, mean_loss - SPEND_DOWN * vit_max) / heal),
            'potions_to_win_flat25': math.ceil(max(
                0.0, mean_loss - SPEND_DOWN * vit_max) / 25.0),
            'hit_pct_mc': (hits / attacks) if attacks else 0.0,
            'dmg_out_per_round': (total_damage_dealt / total_rounds
                                  if total_rounds else 0.0),
        })
    return result

# ----------------------------------------------- #89 expected-value model


def _d20_probs(attacker_dex, defender_dex):
    """Exact d20 outcome probabilities for resolve_hit()'s contest."""
    defense = 10 + defender_dex
    need = defense - attacker_dex           # minimum d20 for success
    n_succ = len([r for r in range(1, 21) if r >= need])
    n_graze = len([r for r in range(1, 21)
                   if need - 3 <= r <= need - 1])
    crit = min(0.25, max(0.05, 0.05 + 0.01 * (attacker_dex - defender_dex)))
    return n_succ / 20.0, n_graze / 20.0, crit


def ev_model(player_level, npc_def, weapon_mid):
    """#89 §1.3's expected-value model, evaluated under CURRENT code
    constants (tier offsets, contest curve, authored stats at the tip).
    Monte Carlo vs this model proves harness fidelity; this model vs #89's
    printed numbers isolates code changed since the survey (v21 B3 #101)."""
    p = reference_player(player_level)
    s_npc = npc_contest_stats(npc_def)
    p_succ, p_graze, crit = _d20_probs(p.stat_dex, s_npc['dex'])
    emult_out = p_succ * (1 + 0.5 * crit) + 0.5 * p_graze
    n_succ_in, n_graze_in, crit_in = _d20_probs(s_npc['dex'], p.stat_dex)
    emult_in = n_succ_in * (1 + 0.5 * crit_in) + 0.5 * n_graze_in
    dmg_out = (weapon_mid + p.stat_str) * emult_out
    return {
        'player_hit_pct': p_succ,
        'npc_hit_pct': n_succ_in,
        'ttk_p_to_n': (npc_def.base_vitality / dmg_out
                       if dmg_out > 0 else float('inf')),
        'dmg_out_per_round': dmg_out,
        'dmg_in_per_round': s_npc['str'] * emult_in,
        'npc_dex': s_npc['dex'], 'npc_str': s_npc['str'],
        'npc_hp': npc_def.base_vitality,
    }


# #89 findings-table values for the validation matchups, transcribed from
# docs/shyland/Shyland_V21_Kill_Feasibility_Survey.md (report at ef3ce6d).
# whistler-below's at-level TTK is derived from the report's own §4 figures
# (260 HP / 15.6 expected damage per round = 16.7 rounds; the §2 row's
# 25.8/5.3 column is L5/L10, not at-level).
V89_ROWS = {
    'black-bear':        {'stats': {'dex': 20, 'str': 12, 'hp': 35},
                          5: {'hit': 0.95, 'ttk': 0.8}},
    'giant-cave-beetle': {'stats': {'dex': 28, 'str': 24, 'hp': 75},
                          5: {'hit': 0.55, 'ttk': 2.7}},
    'mountain-goat':     {'stats': {'dex': 30, 'str': 25, 'hp': 70},
                          10: {'hit': 1.00, 'ttk': 1.1}},
    'buffalo':           {'stats': {'dex': 31, 'str': 26, 'hp': 90},
                          5: {'hit': 0.40, 'ttk': 4.2}},
    'brown-bear':        {'stats': {'dex': 36, 'str': 33, 'hp': 130},
                          10: {'hit': 0.75, 'ttk': 2.7}},
    'whistler-below':    {'stats': {'dex': 36, 'str': 28, 'hp': 260},
                          6: {'hit': 0.25, 'ttk': 16.7}},
}

VALIDATION_MATCHUPS = [
    ('black-bear', 5), ('giant-cave-beetle', 5), ('mountain-goat', 10),
    ('buffalo', 5), ('brown-bear', 10), ('whistler-below', 6),
]


def run_validation(by_slug, weapon_def, n_trials):
    """§4.5.4: bare scenario under #89's model assumptions — stat-less
    Uncommon broadsword (expected midpoint only, no rolled stats, no
    procs), no armor.  The first three matchups are normal-tier (untouched
    by the #101 retune) and must reproduce #89 directly; the brief's three
    named matchups (buffalo, brown-bear, whistler-below) are elite/boss
    and carry the documented retune deltas."""
    mid = expected_midpoint(weapon_def, 1, 'uncommon')
    rows = []
    for slug, level in VALIDATION_MATCHUPS:
        d = by_slug[slug]
        enc = {'id': f'val:{slug}', 'kind': 'solo', 'tier': d.combat_tier,
               'members': [slug], 'at_level': level, 'rooms': []}
        configs = loadout_configs(level, weapon_def, 'uncommon', [],
                                  sample_secondary=False,
                                  statless_weapon=True)
        mc = run_trials(enc, by_slug, configs, n_trials)
        ev = ev_model(level, d, mid)
        ttk_mc = (d.base_vitality / mc['dmg_out_per_round']
                  if mc.get('dmg_out_per_round') else float('inf'))
        rows.append({
            'matchup': f'{slug} @ L{level}',
            'tier': d.combat_tier,
            'v89_printed': V89_ROWS.get(slug, {}).get(level),
            'v89_stats': V89_ROWS.get(slug, {}).get('stats'),
            'current_stats': {'dex': ev['npc_dex'], 'str': ev['npc_str'],
                              'hp': ev['npc_hp']},
            'ev_hit_pct': round(ev['player_hit_pct'], 4),
            'ev_ttk': round(ev['ttk_p_to_n'], 2),
            'mc_hit_pct': round(mc.get('hit_pct_mc', 0.0), 4),
            'mc_ttk_effective': round(ttk_mc, 2),
            'mc_rounds_mean': round(mc.get('rounds_mean', 0.0), 2),
        })
    return rows

# --------------------------------------------------------------- verdicts


def verdict_for(at_row, l10_row):
    """#89's scale verbatim, recomputed under current code + Draught Law.
    (#89 treated at-level hit%% drift from the blessed target as recorded
    calibration noise, never as a verdict demotion — mountain-lion carried
    a -5%% drift and stayed OK — so the potion thresholds decide here too;
    hit%% drift is reported separately, G5 style.)"""
    if at_row is None or not at_row.get('n_resolved'):
        if (l10_row and l10_row.get('n_resolved')
                and l10_row['potions_to_win'] <= STACK_BOUND):
            return 'CLIFF'
        return 'INFEASIBLE'
    pot = at_row['potions_to_win']
    if pot <= 5:
        return 'OK'
    if pot <= 12:
        return 'HARD'
    if pot <= STACK_BOUND:
        return 'CLIFF'
    if (l10_row and l10_row.get('n_resolved')
            and l10_row['potions_to_win'] <= STACK_BOUND):
        return 'CLIFF'
    return 'INFEASIBLE'

# ------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--commit', default='UNKNOWN')
    ap.add_argument('--trials', type=int, default=N_TRIALS)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    random.seed(RNG_SEED)

    # Draught Law spot checks (verification gate 5; #139 test values),
    # through the real seeded EffectDefinition and the real helper.
    draught = EffectDefinition.objects.get(slug='healing-draught')
    comp = draught.components.all()[0]
    frac = comp.computed_magnitude(1)
    checks = {'fraction_mk1': frac,
              'heal_at_718': percent_heal_amount(frac, 718),
              'heal_at_100': percent_heal_amount(frac, 100)}
    print(f'Draught Law spot checks: {checks}', flush=True)
    assert checks['heal_at_718'] == 144, checks
    assert checks['heal_at_100'] == 25, checks

    encounters, by_slug = build_encounters()
    recon = reconciliation()
    print(f"Population: {recon['counts']} of {recon['total']} defs; "
          f"{len(encounters)} encounters", flush=True)

    weapon_def = ItemDefinition.objects.get(slug='broadsword')
    armor_items, armor_table = build_headline_armor(
        two_handed_weapon=weapon_def.is_two_handed)
    print('Headline armor loadout:', flush=True)
    for row in armor_table:
        print(f'  {row}', flush=True)

    print('\n=== Validation vs #89 (spec 4.5.4) ===', flush=True)
    validation = run_validation(by_slug, weapon_def, args.trials)
    for row in validation:
        print(f'  {row}', flush=True)

    scenarios = [
        ('headline', 'uncommon', armor_items, True),
        ('bare', 'uncommon', [], True),
        ('common-weapon', 'common', armor_items, False),
    ]

    results = []
    total_jobs = sum(len({e['at_level'], *REFERENCE_LEVELS})
                     for e in encounters) * len(scenarios)
    done = 0
    for enc in encounters:
        levels = sorted({enc['at_level'], *REFERENCE_LEVELS})
        for level in levels:
            for name, rarity, armor, sample_sec in scenarios:
                configs = loadout_configs(level, weapon_def, rarity, armor,
                                          sample_secondary=sample_sec)
                r = run_trials(enc, by_slug, configs, args.trials)
                r.update({
                    'encounter_id': enc['id'], 'kind': enc['kind'],
                    'tier': enc['tier'],
                    'members': '+'.join(enc['members']),
                    'rooms': ';'.join(enc['rooms']),
                    'encounter_level': enc['at_level'],
                    'player_level': level,
                    'is_at_level': level == enc['at_level'],
                    'scenario': name,
                })
                results.append(r)
                done += 1
                if done % 25 == 0 or done == total_jobs:
                    print(f'  progress {done}/{total_jobs}', flush=True)

    # Verdicts per encounter (headline primary; bare for attribution).
    verdicts = {}
    for enc in encounters:
        vrow = {}
        for scen in ('headline', 'bare'):
            at_row = next((r for r in results
                           if r['encounter_id'] == enc['id']
                           and r['scenario'] == scen and r['is_at_level']),
                          None)
            l10_row = next((r for r in results
                            if r['encounter_id'] == enc['id']
                            and r['scenario'] == scen
                            and r['player_level'] == 10), None)
            vrow[scen] = verdict_for(at_row, l10_row)
        verdicts[enc['id']] = vrow

    # Per-tier aggregation (spec 4.5.1) — at-level, headline scenario.
    tier_sets = {
        'normal': lambda r: r['kind'] == 'solo' and r['tier'] == 'normal',
        'elite': lambda r: r['kind'] == 'solo' and r['tier'] == 'elite',
        'boss': lambda r: r['kind'] == 'solo' and r['tier'] == 'boss',
        'boss-encounter': lambda r: r['kind'] == 'boss-group',
        'multi-aggro': lambda r: r['kind'] == 'multi-aggro',
    }
    tier_table = {}
    for tier, pred in tier_sets.items():
        rows = [r for r in results
                if pred(r) and r['is_at_level'] and r['scenario'] == 'headline'
                and r.get('n_resolved')]
        if rows:
            tier_table[tier] = {
                'encounters': len(rows),
                'hp_loss_frac_mean': statistics.fmean(
                    r['hp_loss_frac_mean'] for r in rows),
                'draughts_per_fight_mean': statistics.fmean(
                    r['draughts_per_fight'] for r in rows),
                'draught_cost_cp_mean': statistics.fmean(
                    r['draught_cost_cp'] for r in rows),
            }
    print('\n=== Per-tier aggregation (at-level, headline) ===', flush=True)
    for tier, row in tier_table.items():
        print(f'  {tier}: {row}', flush=True)

    # CSV dataset.
    csv_path = os.path.join(args.out, 'dataset.csv')
    fields = ['encounter_id', 'kind', 'tier', 'members', 'rooms',
              'encounter_level', 'player_level', 'is_at_level', 'scenario',
              'n_trials', 'n_resolved', 'unwinnable_fraction',
              'vitality_max', 'draught_heal',
              'hp_loss_mean', 'hp_loss_std', 'hp_loss_p10', 'hp_loss_p90',
              'hp_loss_frac_mean', 'rounds_mean', 'rounds_std',
              'p_death_unhealed', 'draughts_per_fight', 'draught_cost_cp',
              'potions_to_win', 'potions_to_win_flat25', 'hit_pct_mc']
    with open(csv_path, 'w', newline='') as fh:
        fh.write(f'# Shyland V24.1 fight-cost survey dataset (#180) — '
                 f'commit {args.commit}, RNG seed {RNG_SEED}, '
                 f'N={args.trials} trials per row\n')
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore',
                           restval='')
        w.writeheader()
        for r in results:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v)
                        for k, v in r.items() if k in fields})

    summary = {
        'commit': args.commit, 'rng_seed': RNG_SEED, 'n_trials': args.trials,
        'draught_spot_checks': checks,
        'reconciliation': recon,
        'encounter_count': len(encounters),
        'row_count': len(results),
        'armor_loadout': armor_table,
        'validation': validation,
        'tier_table': tier_table,
        'verdicts': verdicts,
        'blessed_targets': BLESSED_TARGET,
        'npc_tier_offset': dict(NPC_TIER_OFFSET),
        'contest_curve': {'base': NPC_CONTEST_BASE, 'step': NPC_CONTEST_STEP},
        'encounters': [{k: enc[k] for k in
                        ('id', 'kind', 'tier', 'members', 'at_level', 'rooms')}
                       for enc in encounters],
    }
    with open(os.path.join(args.out, 'summary.json'), 'w') as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f'\nWrote {csv_path} ({len(results)} rows) and summary.json',
          flush=True)


if __name__ == '__main__':
    main()
