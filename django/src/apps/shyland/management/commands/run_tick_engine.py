import asyncio
import logging
import random

from channels.db import database_sync_to_async
from django.core.management.base import BaseCommand

from apps.shyland.envelope import envelope_ts

logger = logging.getLogger('shyland.tick')

# Lore-only escalation ladder for the dying window. No numerals, no time
# units — the design calls for atmosphere, not a countdown.
DYING_LADDER = [
    (5,  "The cold is spreading. Your heartbeat is slowing."),
    (10, "The world is growing dim at the edges. You are running out of time."),
    (15, "Your thoughts drift. It would be so easy to let go."),
    (20, "You can barely feel your body now. Something vast is waiting."),
    (25, "The last of your strength is nearly gone. Act now, or not at all."),
    (26, "Your vision narrows to a single point of light."),
    (27, "The light is fading."),
    (28, "So faint now."),
    (29, "Darkness."),
]


class Command(BaseCommand):
    help = 'Run the Shyland tick engine (1-second loop).'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # character_pk -> set of ladder thresholds already sent. In-memory
        # only: an engine restart loses it, but the elapsed-based check in
        # process_dying_ladder reseeds from the character's current elapsed
        # time on next sight, so no lines are replayed or skipped.
        self._dying_ladder_sent = {}
        # npc_instance_pk -> DialogueResponse pk last delivered by that NPC.
        # In-memory only, per v19 brief 9: guarantees no *consecutive*
        # self-repeat; an engine restart just loses the memory, which is
        # an accepted tradeoff (not a global-novelty guarantee anyway).
        self._last_dialogue_response = {}

    def handle(self, *args, **options):
        self.stdout.write('Tick engine starting.')
        asyncio.run(self.tick_loop())

    async def tick_loop(self):
        tick_number = 0
        while True:
            tick_number += 1
            await self.process_tick(tick_number)
            await asyncio.sleep(1)

    async def process_tick(self, tick_number):
        await self.process_combat(tick_number)
        await self.process_corpse_decay()
        await self.process_npc_respawn()
        await self.process_effects(tick_number)
        await self.process_dying_ladder()
        await self.process_dialogue_delivery()

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    async def process_combat(self, tick_number):
        import random
        from datetime import timedelta
        from django.utils import timezone
        from channels.db import database_sync_to_async as _dsa
        from apps.shyland.models import (
            CombatSession, CombatAction, NpcInstance, Character,
            COMBAT_ROUND_TICKS, DYING_DURATION_SECS, STALE_SESSION_SECS,
        )
        from apps.shyland.combat_utils import (
            get_npc_stats, roll_initiative, resolve_hit, calculate_damage,
            get_npc_health_description, apply_death_penalties,
            apply_npc_effects, xp_for_kill, npc_display_name,
        )
        from apps.shyland.item_utils import create_corpse, get_durability_penalty

        now = timezone.now()

        def resolve_focus_npc(session, npc_list):
            """Session's focus_npc if set, alive, and still in npc_list;
            otherwise the first npc (fallback for unset/stale focus)."""
            if not npc_list:
                return None
            if session.focus_npc_id is not None:
                match = next((n for n in npc_list if n.pk == session.focus_npc_id), None)
                if match is not None:
                    return match
            return npc_list[0]

        # --- Stale session cleanup ---
        @_dsa
        def get_stale_sessions():
            cutoff = now - timedelta(seconds=STALE_SESSION_SECS)
            return list(CombatSession.objects.filter(
                is_active=True,
                last_tick_at__lt=cutoff,
            ))

        @_dsa
        def close_session(session):
            """Close the session and return one (char_pk, status) pair per
            member — v20 brief 4 (#2): disengagement ends combat for the
            player, so the fight pane and combat-red state must clear."""
            session.is_active = False
            session.save(update_fields=['is_active'])
            chars = list(session.characters.select_related(
                'current_room__area', 'current_room__zone',
            ).all())
            return [(c.pk, self._build_status(c)) for c in chars]

        # v20 brief 4 (#2): the fight-info feed. One payload per session
        # member, sent every engine tick; when the session has just ended,
        # the payload clears the pane and a fresh status clears combat-red.
        @_dsa
        def build_fight_payloads(session):
            chars = list(session.characters.select_related(
                'current_room__area', 'current_room__zone',
            ).all())
            if not session.is_active:
                return [
                    (c.pk, {'type': 'fight', 'active': False, 'enemies': []},
                     self._build_status(c))
                    for c in chars
                ]
            npc_list = list(session.npcs.select_related('definition')
                            .filter(is_alive=True))
            focus_pk = session.focus_npc_id
            if focus_pk is None or all(n.pk != focus_pk for n in npc_list):
                focus_pk = npc_list[0].pk if npc_list else None
            enemies = [
                {
                    'name': npc_display_name(n, npc_list),
                    'hp': n.vitality_current,
                    'hp_max': n.vitality_max,
                    'focused': n.pk == focus_pk,
                }
                for n in npc_list
            ]
            return [
                (c.pk, {'type': 'fight', 'active': True, 'enemies': enemies},
                 None)
                for c in chars
            ]

        async def send_fight_payloads(session):
            for char_pk, fight, status in await build_fight_payloads(session):
                await self.send_to_player(char_pk, '', None, status, fight=fight)

        stale = await get_stale_sessions()
        for session in stale:
            payloads = await close_session(session)
            for char_pk, status in payloads:
                await self.send_to_player(
                    char_pk, '', None, status,
                    fight={'type': 'fight', 'active': False, 'enemies': []},
                )
            logger.info(f"Combat session {session.pk} closed (stale)")

        # --- Dying state expiry ---
        @_dsa
        def get_expired_dying():
            cutoff = now - timedelta(seconds=DYING_DURATION_SECS)
            return list(Character.objects.filter(
                is_dying=True,
                dying_since__lte=cutoff,
            ).select_related('recall_room__zone', 'recall_room__area'))

        @_dsa
        def execute_death(character):
            broken = apply_death_penalties(character)
            recall = character.recall_room
            character.is_dying = False
            character.dying_since = None
            character.is_dead = False
            character.current_room = recall
            character.vitality_current = character.vitality_max
            character.acuity_current = character.acuity_baseline
            character.longevity_current = character.longevity_max
            character.save(update_fields=[
                'is_dying', 'dying_since', 'is_dead', 'current_room',
                'vitality_current', 'acuity_current', 'longevity_current',
            ])
            active_instances = list(character.active_effects.filter(is_active=True))
            for ei in active_instances:
                ei.component_instances.filter(is_active=True).update(
                    is_active=False, removed_by='death'
                )
            character.active_effects.filter(is_active=True).update(
                is_active=False, removed_by='death'
            )
            CombatAction.objects.filter(character=character, is_processed=False).delete()
            for session in character.combat_sessions.filter(is_active=True):
                session.characters.remove(character)
                if session.characters.count() == 0:
                    session.is_active = False
                    session.save(update_fields=['is_active'])
                    session.npcs.clear()
            return broken, recall

        dying_chars = await get_expired_dying()
        for character in dying_chars:
            broken, recall = await execute_death(character)
            name = character.name
            await self.send_to_player(character.pk, "The darkness takes you.", 'error', None)
            msg = f"You have died and awakened at {recall.name if recall else 'your recall point'}."
            if broken:
                msg += f" Your {', '.join(broken)} {'has' if len(broken) == 1 else 'have'} broken."
            # v20 brief 4: location of the recall room (#1); death always
            # ends combat membership (#2), so in_combat is False and the
            # fight pane clears.
            recall_zone = recall.zone if recall else None
            recall_area = recall.area if recall and recall.area_id else None
            status_payload = {
                'type': 'status',
                'character_name': character.name,
                'vitality': character.vitality_current,
                'vitality_max': character.vitality_max,
                'acuity': round(character.acuity_current, 2),
                'acuity_baseline': round(character.acuity_baseline, 2),
                'acuity_band_low': round(character.acuity_band_low, 2),
                'acuity_band_high': round(character.acuity_band_high, 2),
                'longevity': character.longevity_current,
                'longevity_max': character.longevity_max,
                'room_name': recall.name if recall else '',
                'zone_name': recall_zone.name if recall_zone else '',
                'zone_color': recall_zone.theme_color if recall_zone else '#CCCCCC',
                'area_name': recall_area.name if recall_area else None,
                'area_color': recall_area.theme_color if recall_area else None,
                'in_combat': False,
            }
            await self.send_to_player(
                character.pk, msg, 'system', status_payload, event='respawn',
                fight={'type': 'fight', 'active': False, 'enemies': []},
            )
            logger.info(f"Character {name} died and respawned at room {recall.pk if recall else 'None'}")

        # --- Active combat sessions ---
        @_dsa
        def get_active_sessions():
            return list(CombatSession.objects.filter(is_active=True).prefetch_related(
                'characters__active_effects',
                'npcs__definition__effects__effect_definition',
            ))

        @_dsa
        def update_session_tick(session):
            session.tick_counter += 1
            session.last_tick_at = now
            session.save(update_fields=['tick_counter', 'last_tick_at'])
            return session.tick_counter

        sessions = await get_active_sessions()

        for session in sessions:
            tick_counter = await update_session_tick(session)

            if tick_counter % COMBAT_ROUND_TICKS != 0:
                # v20 brief 4 (#2): the fight feed updates every engine
                # tick, not only on round boundaries.
                await send_fight_payloads(session)
                continue

            @_dsa
            def load_participants(session):
                chars = list(session.characters.select_related(
                    'current_room__area', 'current_room__zone',
                    'archetype__unarmed_message_pool',
                ).prefetch_related(
                    'archetype__unarmed_message_pool__messages',
                ).all())
                npcs = list(session.npcs.select_related(
                    'definition',
                    'definition__unarmed_message_pool',
                ).prefetch_related(
                    'definition__effects__effect_definition',
                    'definition__unarmed_message_pool__messages',
                ).all())
                return chars, npcs

            characters, npcs = await load_participants(session)

            # Defense in depth: an unattackable NPC must never hold aggro or
            # take a combat turn. It should never reach a CombatSession's npc
            # set (excluded at aggro/attack time), but if one does, drop it
            # here rather than letting it act or be targeted.
            safe_npcs = []
            for npc in npcs:
                if not npc.definition.attackable:
                    logger.warning(
                        f"Unattackable NPC {npc.definition.slug} (instance {npc.pk}) "
                        f"found in CombatSession {session.pk}; skipping."
                    )
                    continue
                safe_npcs.append(npc)
            npcs = safe_npcs

            if not characters or not npcs:
                payloads = await close_session(session)
                for char_pk, status in payloads:
                    await self.send_to_player(
                        char_pk, '', None, status,
                        fight={'type': 'fight', 'active': False, 'enemies': []},
                    )
                continue

            character = characters[0]

            @_dsa
            def load_player_actions(session, character):
                return list(CombatAction.objects.filter(
                    combat_session=session,
                    character=character,
                    is_processed=False,
                ).order_by('queued_at'))

            @_dsa
            def generate_npc_actions(session, npcs, character):
                actions = []
                for npc in npcs:
                    action = CombatAction.objects.create(
                        combat_session=session,
                        npc=npc,
                        action_type=CombatAction.ACTION_ATTACK,
                        target_character=character,
                    )
                    actions.append(action)
                return actions

            player_actions = await load_player_actions(session, character)
            npc_actions = await generate_npc_actions(session, npcs, character)

            if not player_actions and npcs and not character.is_dying:
                @_dsa
                def create_auto_attack(session, character, npc):
                    return CombatAction.objects.create(
                        combat_session=session,
                        character=character,
                        action_type=CombatAction.ACTION_ATTACK,
                        target_npc=npc,
                    )
                auto_target = resolve_focus_npc(session, npcs)
                player_actions = [await create_auto_attack(session, character, auto_target)]

            is_first_round = (tick_counter == COMBAT_ROUND_TICKS)
            first_attacker = session.first_attacker

            if is_first_round:
                if first_attacker == 'character':
                    ordered_actions = player_actions + npc_actions
                else:
                    ordered_actions = npc_actions + player_actions
            else:
                char_init = roll_initiative(character.stat_dex, character.stat_per)
                avg_npc_init = (
                    sum(
                        roll_initiative(get_npc_stats(n)['dex'], get_npc_stats(n)['per'])
                        for n in npcs
                    ) / len(npcs)
                ) if npcs else 0
                if char_init >= avg_npc_init:
                    ordered_actions = player_actions + npc_actions
                else:
                    ordered_actions = npc_actions + player_actions

            @_dsa
            def execute_actions(session, ordered_actions, character, npcs):
                import random as _random
                from datetime import timedelta as _td
                from django.utils import timezone as _tz
                from apps.shyland.models import (
                    CombatAction, ItemInstance, STAT_POINTS_PER_LEVEL,
                )
                from apps.shyland.combat_utils import (
                    get_npc_stats, resolve_hit, calculate_damage,
                    acuity_damage_modifier,
                    get_npc_health_description, apply_npc_effects, xp_for_kill,
                    xp_for_next_level, recalculate_bars, get_unarmed_message,
                    npc_display_name,
                )
                from apps.shyland.item_utils import get_durability_penalty, create_corpse

                _now = _tz.now()
                messages = []
                statuses = []
                room_messages = []

                live_npcs = list(npcs)
                focus_npc = resolve_focus_npc(session, live_npcs)
                focus_npc_pk = focus_npc.pk if focus_npc else None

                for action in ordered_actions:
                    if action.is_processed:
                        continue
                    CombatAction.objects.filter(pk=action.pk).update(is_processed=True)

                    # --- Character attacks NPC ---
                    if action.character_id and action.target_npc_id:
                        if character.is_dying:
                            # Falling discards this character's own attacks from
                            # the moment of falling onward — no posthumous kills.
                            continue
                        npc = next((n for n in live_npcs if n.pk == action.target_npc_id), None)
                        if npc is None or not npc.is_alive:
                            continue

                        display = npc_display_name(npc, live_npcs)

                        equipped_weapons = list(ItemInstance.objects.filter(
                            owner=character,
                            is_equipped=True,
                            definition__item_type='weapon',
                            is_broken=False,
                        ).select_related('definition'))
                        weapon_item = equipped_weapons[0] if equipped_weapons else None

                        npc_stats = get_npc_stats(npc)
                        hit_result = resolve_hit(character.stat_dex, npc_stats['dex'])

                        if hit_result == 'miss':
                            messages.append((character.pk, f"You miss {display}.", 'combat', None))
                            continue

                        if weapon_item:
                            defn = weapon_item.definition
                            spread = weapon_item.damage_spread or 0
                            base_damage = _random.uniform(
                                weapon_item.damage_midpoint - spread,
                                weapon_item.damage_midpoint + spread,
                            )
                            stat_bonus = character.stat_str if not defn.is_ranged else character.stat_dex
                            dur_mod = 1.0 - get_durability_penalty(weapon_item)
                        else:
                            base_damage = _random.uniform(1, 3)
                            stat_bonus = character.stat_str
                            dur_mod = 1.0

                        is_focus = (npc.pk == focus_npc_pk)
                        acuity_mod = acuity_damage_modifier(character)
                        damage = calculate_damage(base_damage, stat_bonus, acuity_mod, dur_mod, hit_result, is_focus_target=is_focus)
                        damage_int = max(1, int(damage))

                        npc.vitality_current = max(0, npc.vitality_current - damage_int)
                        npc.save(update_fields=['vitality_current'])

                        if weapon_item:
                            if hit_result == 'critical':
                                flavor = f"You land a critical hit on {display}"
                            else:
                                flavor = f"You hit {display}"
                        else:
                            pool = character.archetype.unarmed_message_pool if character.archetype_id else None
                            raw = get_unarmed_message(pool, display)
                            flavor = raw.rstrip('.')
                            if hit_result == 'critical':
                                flavor = f"[Critical] {flavor}"

                        msg = f"{flavor} for {damage_int} damage."
                        health_desc = get_npc_health_description(npc.vitality_current, npc.vitality_max)
                        msg += f" {display[0].upper()}{display[1:]} {health_desc}."
                        messages.append((character.pk, msg, 'combat', None))

                        if npc.vitality_current <= 0:
                            npc.is_alive = False
                            npc_def = npc.definition
                            npc.respawn_at = _now + _td(minutes=npc_def.respawn_minutes)
                            npc.save(update_fields=['is_alive', 'respawn_at'])

                            xp = xp_for_kill(npc, character)
                            character.xp += xp
                            character.save(update_fields=['xp'])

                            create_corpse(npc, character)

                            messages.append((character.pk, f"You have slain {display}! (+{xp} XP)", 'combat', None))
                            room_messages.append((session.room_id, f"{character.name} has slain the {npc.definition.name}!", 'combat', character.pk))
                            if npc_def.death_message:
                                room_messages.append((session.room_id, npc_def.death_message, 'combat', None))

                            while character.xp >= xp_for_next_level(character.level):
                                character.level += 1
                                character.unspent_stat_points += STAT_POINTS_PER_LEVEL
                                new_vit_max, new_lon_max = recalculate_bars(character)
                                character.save(update_fields=[
                                    'level', 'unspent_stat_points',
                                    'vitality_max', 'vitality_current',
                                    'longevity_max', 'longevity_current',
                                ])
                                pts = character.unspent_stat_points
                                messages.append((character.pk,
                                    f"*** You have reached level {character.level}! "
                                    f"Your Vitality is now {new_vit_max} and your Longevity is now {new_lon_max}. "
                                    f"You have {pts} unspent stat point{'s' if pts != 1 else ''}. "
                                    f"Type 'spend' to allocate them.",
                                    'system', None
                                ))

                            statuses.append((character.pk, self._build_status(character)))

                            live_npcs = [n for n in live_npcs if n.pk != npc.pk]
                            session.npcs.remove(npc)

                            if not live_npcs:
                                session.is_active = False
                                session.focus_npc = None
                                session.save(update_fields=['is_active', 'focus_npc'])
                                messages.append((character.pk, "Combat has ended.", 'system', None))
                                break

                            if npc.pk == focus_npc_pk:
                                new_focus = live_npcs[0]
                                session.focus_npc = new_focus
                                session.save(update_fields=['focus_npc'])
                                focus_npc_pk = new_focus.pk
                                focus_name = npc_display_name(new_focus, live_npcs)
                                messages.append((character.pk, f"You turn your attacks on {focus_name}.", 'combat', None))

                    # --- NPC attacks character ---
                    elif action.npc_id and action.target_character_id:
                        npc = next((n for n in live_npcs if n.pk == action.npc_id), None)
                        if npc is None or not npc.is_alive:
                            continue
                        if character.is_dying:
                            continue

                        npc_stats = get_npc_stats(npc)
                        hit_result = resolve_hit(npc_stats['dex'], character.stat_dex)

                        if hit_result == 'miss':
                            messages.append((character.pk, f"The {npc.definition.name} misses you.", 'combat', None))
                            continue

                        base_damage = _random.uniform(
                            npc_stats['str'] * 0.8,
                            npc_stats['str'] * 1.2,
                        )
                        damage = calculate_damage(base_damage, 0, 1.0, 1.0, hit_result, is_focus_target=True)
                        damage_int = max(1, int(damage))

                        character.vitality_current = max(0, character.vitality_current - damage_int)

                        if character.vitality_current <= 0:
                            # Falling replaces all combat output for this player —
                            # no hit line for the killing blow either. Effects on
                            # the character are canceled and their own queued
                            # attacks are discarded from this moment onward.
                            character.vitality_current = 0
                            character.is_dying = True
                            character.dying_since = _now
                            character.save(update_fields=['vitality_current', 'is_dying', 'dying_since'])

                            active_instances = list(character.active_effects.filter(is_active=True))
                            for ei in active_instances:
                                ei.component_instances.filter(is_active=True).update(
                                    is_active=False, removed_by='dying'
                                )
                            character.active_effects.filter(is_active=True).update(
                                is_active=False, removed_by='dying'
                            )
                            CombatAction.objects.filter(character=character, is_processed=False).delete()

                            messages.append((character.pk, '', None, 'clear'))
                            messages.append((character.pk,
                                "You have been dealt a fatal blow. Your life force is ebbing away — "
                                "you have only moments to act.",
                                'error', 'dying'))
                            room_messages.append((session.room_id,
                                f"{character.name} has fallen and is dying!", 'combat', character.pk))
                        else:
                            character.save(update_fields=['vitality_current'])

                            npc_pool = npc.definition.unarmed_message_pool
                            raw = get_unarmed_message(
                                npc_pool, character.name,
                                attacker_name=npc.definition.name,
                                fallback_slug='npc-default',
                            )
                            flavor = raw.rstrip('.')
                            if hit_result == 'critical':
                                msg = f"[Critical] {flavor} for {damage_int} damage!"
                            else:
                                msg = f"{flavor} for {damage_int} damage."

                            effect_msgs = apply_npc_effects(npc, character)
                            if effect_msgs:
                                msg += " " + " and ".join(effect_msgs) + "."

                            messages.append((character.pk, msg, 'combat', None))

                        statuses.append((character.pk, self._build_status(character)))

                return messages, statuses, room_messages

            messages, statuses, room_messages = await execute_actions(
                session, ordered_actions, character, npcs
            )

            for char_pk, text, category, event in messages:
                await self.send_to_player(char_pk, text, category, None, event=event)
            for char_pk, status in statuses:
                await self.send_to_player(char_pk, '', 'status', status)
            for room_id, text, category, exclude_pk in room_messages:
                await self.broadcast_to_room(room_id, text, category, exclude_pk=exclude_pk)

            # v20 brief 4 (#2): fight feed after the round resolves — enemy
            # hp is current, and if the round ended the session (victory)
            # the payload clears the pane and the combat-red state.
            await send_fight_payloads(session)

    # ------------------------------------------------------------------
    # Corpse decay
    # ------------------------------------------------------------------

    async def process_corpse_decay(self):
        from django.utils import timezone
        now = timezone.now()
        expired = await self.get_expired_corpses(now)

        for corpse in expired:
            name = corpse.npc_name_snapshot
            room_id = corpse.current_room_id
            await self.delete_corpse(corpse.pk)
            await self.broadcast_to_room(
                room_id,
                f"The corpse of {name} slowly crumbles to nothing.",
                category='room',
            )
            logger.info(f"Corpse decayed: {name} in room {room_id}")

    @database_sync_to_async
    def get_expired_corpses(self, now):
        from apps.shyland.models import Corpse
        return list(Corpse.objects.filter(decay_at__lte=now).select_related('npc_definition'))

    @database_sync_to_async
    def delete_corpse(self, pk):
        from apps.shyland.models import Corpse
        Corpse.objects.filter(pk=pk).delete()

    # ------------------------------------------------------------------
    # NPC respawn
    # ------------------------------------------------------------------

    async def process_npc_respawn(self):
        from django.utils import timezone
        now = timezone.now()
        spawns = await self.get_active_spawns()

        for spawn in spawns:
            await self.clear_expired_dead(spawn, now)
            if spawn.requires_living_npc_id and not await self.gate_npc_is_alive(spawn):
                continue
            live_count, dead_count = await self.count_instances(spawn)
            # Dead instances hold their slot until clear_expired_dead removes
            # them at respawn time; counting only live instances here would
            # refill the room the tick after a kill and respawn_minutes would
            # never matter.
            to_create = min(
                spawn.count - (live_count + dead_count),
                (spawn.count * 2) - (live_count + dead_count),
            )
            for _ in range(to_create):
                await self.create_live_instance(spawn)
                logger.info(
                    f"NPC spawned: {spawn.npc_definition.name} "
                    f"(Mk {spawn.mk_tier}) in room {spawn.room.name}"
                )

    @database_sync_to_async
    def get_active_spawns(self):
        from apps.shyland.models import RoomSpawn
        return list(RoomSpawn.objects.filter(is_active=True).select_related('npc_definition', 'room'))

    @database_sync_to_async
    def clear_expired_dead(self, spawn, now):
        from apps.shyland.models import NpcInstance
        NpcInstance.objects.filter(
            definition=spawn.npc_definition,
            spawn_room=spawn.room,
            mk_tier=spawn.mk_tier,
            is_alive=False,
            respawn_at__lte=now,
        ).delete()

    @database_sync_to_async
    def gate_npc_is_alive(self, spawn):
        from apps.shyland.models import NpcInstance
        return NpcInstance.objects.filter(
            definition_id=spawn.requires_living_npc_id,
            current_room=spawn.room,
            is_alive=True,
        ).exists()

    @database_sync_to_async
    def count_instances(self, spawn):
        from apps.shyland.models import NpcInstance
        qs = NpcInstance.objects.filter(
            definition=spawn.npc_definition,
            spawn_room=spawn.room,
            mk_tier=spawn.mk_tier,
        )
        live_count = qs.filter(is_alive=True).count()
        dead_count = qs.filter(is_alive=False).count()
        return live_count, dead_count

    @database_sync_to_async
    def create_live_instance(self, spawn):
        from apps.shyland.models import NpcInstance
        NpcInstance.objects.create(
            definition=spawn.npc_definition,
            current_room=spawn.room,
            spawn_room=spawn.room,
            mk_tier=spawn.mk_tier,
            vitality_current=spawn.npc_definition.base_vitality,
            vitality_max=spawn.npc_definition.base_vitality,
            is_alive=True,
        )

    # ------------------------------------------------------------------
    # Effects: per-tick DoT/HoT, Acuity drift, expiry
    # ------------------------------------------------------------------

    async def process_effects(self, tick_number):
        from collections import defaultdict
        from django.utils import timezone
        from django.db.models import F
        from apps.shyland.models import (
            EffectComponentInstance, Character,
            COMBAT_ROUND_TICKS, ACUITY_DRIFT_RATE,
        )
        from apps.shyland.effect_utils import apply_stat_effect, _expiry_message_for_effect, _expiry_message_for_component

        now = timezone.now()
        is_round_boundary = (tick_number % COMBAT_ROUND_TICKS == 0)

        TICKING_TYPES = {
            'dot_vitality', 'dot_acuity', 'dot_longevity',
            'hot_vitality', 'hot_acuity', 'hot_longevity',
            'shift_acuity_high', 'shift_acuity_low',
        }

        # ---- Phase 1: Component ticking (round boundaries only) ----
        if is_round_boundary:
            @database_sync_to_async
            def get_ticking_component_instances():
                return list(EffectComponentInstance.objects.filter(
                    is_active=True,
                    component__component_type__in=TICKING_TYPES,
                ).select_related(
                    'component',
                    'effect_instance__target__current_room__area',
                    'effect_instance__target__current_room__zone',
                    'effect_instance__definition',
                ))

            @database_sync_to_async
            def fall_and_cancel(char):
                char.save(update_fields=['vitality_current', 'is_dying', 'dying_since'])
                active_instances = list(char.active_effects.filter(is_active=True))
                for ei in active_instances:
                    ei.component_instances.filter(is_active=True).update(
                        is_active=False, removed_by='dying'
                    )
                char.active_effects.filter(is_active=True).update(
                    is_active=False, removed_by='dying'
                )
                from apps.shyland.models import CombatAction
                CombatAction.objects.filter(character=char, is_processed=False).delete()

            ticking = await get_ticking_component_instances()

            # Characters who fell to a component processed earlier in this
            # same phase: skip any further ticking components on them this
            # tick (their effects are already canceled — a second component
            # of the same effect must not still apply/message).
            newly_dying = set()

            for ci in ticking:
                character = ci.effect_instance.target
                if character.pk in newly_dying:
                    continue
                definition = ci.effect_instance.definition
                ctype = ci.component.component_type
                magnitude = ci.magnitude

                if ctype == 'dot_vitality':
                    character.vitality_current = max(0, character.vitality_current - magnitude)
                    if character.vitality_current <= 0:
                        character.vitality_current = 0
                        character.is_dying = True
                        character.dying_since = now
                        newly_dying.add(character.pk)

                        await fall_and_cancel(character)

                        await self.send_to_player(character.pk, '', None, None, event='clear')
                        await self.send_to_player(
                            character.pk,
                            "You have been dealt a fatal blow. Your life force is ebbing away — "
                            "you have only moments to act.",
                            'error', await self._build_status_async(character), event='dying',
                        )
                        await self.broadcast_to_room(
                            character.current_room_id,
                            f"{character.name} has fallen and is dying!", 'combat',
                            exclude_pk=character.pk,
                        )
                    else:
                        await database_sync_to_async(character.save)(update_fields=['vitality_current'])
                        status = await self._build_status_async(character)
                        await self.send_to_player(
                            character.pk,
                            f"You take {int(magnitude)} damage from {definition.name}.", 'combat',
                            status,
                        )

                elif ctype == 'dot_longevity':
                    character.longevity_current = max(0, character.longevity_current - magnitude)
                    await database_sync_to_async(character.save)(update_fields=['longevity_current'])
                    status = await self._build_status_async(character)
                    await self.send_to_player(
                        character.pk,
                        f"Your stamina drains from {definition.name}. (-{int(magnitude)} Longevity)",
                        'combat', status,
                    )

                elif ctype == 'dot_acuity':
                    character.acuity_current = round(
                        max(0.1, min(1.9, character.acuity_current - magnitude)), 1
                    )
                    await database_sync_to_async(character.save)(update_fields=['acuity_current'])
                    status = await self._build_status_async(character)
                    await self.send_to_player(
                        character.pk,
                        f"Your focus is disrupted by {definition.name}. "
                        f"(Acuity {character.acuity_current:.1f})",
                        'combat', status,
                    )

                elif ctype == 'hot_vitality':
                    character.vitality_current = min(
                        character.vitality_current + magnitude, character.vitality_max
                    )
                    await database_sync_to_async(character.save)(update_fields=['vitality_current'])
                    status = await self._build_status_async(character)
                    await self.send_to_player(
                        character.pk,
                        f"You recover {int(magnitude)} Vitality from {definition.name}.",
                        'system', status,
                    )

                elif ctype == 'hot_longevity':
                    character.longevity_current = min(
                        character.longevity_current + magnitude, character.longevity_max
                    )
                    await database_sync_to_async(character.save)(update_fields=['longevity_current'])
                    status = await self._build_status_async(character)
                    await self.send_to_player(
                        character.pk,
                        f"You recover {int(magnitude)} Longevity from {definition.name}.",
                        'system', status,
                    )

                elif ctype == 'hot_acuity':
                    diff = character.acuity_baseline - character.acuity_current
                    step = min(abs(diff), magnitude) * (1 if diff >= 0 else -1)
                    character.acuity_current = round(
                        max(0.1, min(1.9, character.acuity_current + step)), 1
                    )
                    await database_sync_to_async(character.save)(update_fields=['acuity_current'])
                    status = await self._build_status_async(character)
                    await self.send_to_player(
                        character.pk,
                        f"Your mind clears from {definition.name}. "
                        f"(Acuity {character.acuity_current:.1f})",
                        'system', status,
                    )

                elif ctype == 'shift_acuity_high':
                    character.acuity_current = round(
                        max(0.1, min(1.9, character.acuity_current + magnitude)), 1
                    )
                    await database_sync_to_async(character.save)(update_fields=['acuity_current'])
                    status = await self._build_status_async(character)
                    await self.send_to_player(
                        character.pk,
                        f"Your focus sharpens. (Acuity {character.acuity_current:.1f})",
                        'system', status,
                    )

                elif ctype == 'shift_acuity_low':
                    character.acuity_current = round(
                        max(0.1, min(1.9, character.acuity_current - magnitude)), 1
                    )
                    await database_sync_to_async(character.save)(update_fields=['acuity_current'])
                    status = await self._build_status_async(character)
                    await self.send_to_player(
                        character.pk,
                        f"Your focus wavers. (Acuity {character.acuity_current:.1f})",
                        'system', status,
                    )

        # ---- Phase 2: Passive Acuity drift (every tick) ----
        @database_sync_to_async
        def get_characters_needing_drift():
            candidates = list(Character.objects.exclude(
                acuity_current=F('acuity_baseline')
            ))

            acuity_shift_types = {'shift_acuity_high', 'shift_acuity_low'}
            result = []
            for char in candidates:
                has_shift = EffectComponentInstance.objects.filter(
                    effect_instance__target=char,
                    is_active=True,
                    component__component_type__in=acuity_shift_types,
                ).exists()
                if not has_shift:
                    result.append(char)
            return result

        @database_sync_to_async
        def save_acuity(char, val):
            char.acuity_current = val
            char.save(update_fields=['acuity_current'])

        drift_characters = await get_characters_needing_drift()

        for character in drift_characters:
            baseline = character.acuity_baseline
            current = character.acuity_current
            diff = baseline - current

            if abs(diff) <= ACUITY_DRIFT_RATE:
                new_acuity = baseline
            elif diff > 0:
                new_acuity = round(current + ACUITY_DRIFT_RATE, 2)
            else:
                new_acuity = round(current - ACUITY_DRIFT_RATE, 2)

            new_acuity = round(max(0.1, min(1.9, new_acuity)), 2)
            await save_acuity(character, new_acuity)

        # ---- Phase 3: Component expiry (every tick) ----
        @database_sync_to_async
        def get_expiring_component_instances():
            return list(EffectComponentInstance.objects.filter(
                is_active=True,
                expires_at__lte=now,
            ).select_related(
                'component',
                'effect_instance__target',
                'effect_instance__definition',
            ))

        @database_sync_to_async
        def count_active_cis_on_instance(parent):
            return EffectComponentInstance.objects.filter(
                effect_instance=parent, is_active=True
            ).count()

        @database_sync_to_async
        def expire_ci(ci):
            ci.is_active = False
            ci.removed_by = 'timeout'
            ci.save(update_fields=['is_active', 'removed_by'])

        @database_sync_to_async
        def close_instance(parent):
            parent.is_active = False
            parent.removed_by = 'timeout'
            parent.save(update_fields=['is_active', 'removed_by'])

        @database_sync_to_async
        def reverse_stat_ci(character, ci):
            apply_stat_effect(character, ci, reverse=True)

        expiring = await get_expiring_component_instances()

        by_instance = defaultdict(list)
        for ci in expiring:
            by_instance[ci.effect_instance_id].append(ci)

        for effect_instance_id, cis in by_instance.items():
            parent = cis[0].effect_instance
            total_active = await count_active_cis_on_instance(parent)
            all_expiring_now = (total_active == len(cis))

            for ci in cis:
                character = parent.target
                ctype = ci.component.component_type

                if ctype in ('stat_bonus', 'stat_penalty'):
                    await reverse_stat_ci(character, ci)

                await expire_ci(ci)

                if not all_expiring_now:
                    msg = _expiry_message_for_component(ci, parent.definition.name)
                    if msg:
                        await self.send_to_player(character.pk, msg, 'system', None)

            if all_expiring_now:
                msg = _expiry_message_for_effect(parent)
                if msg:
                    await self.send_to_player(parent.target.pk, msg, 'system', None)

            remaining = await count_active_cis_on_instance(parent)
            if remaining == 0:
                await close_instance(parent)
                logger.info(
                    f"EffectInstance closed: {parent.definition.slug} on {parent.target.name}"
                )

        # ---- Phase 4: Passive bar regeneration (every tick) ----
        import math
        from apps.shyland.models import VITALITY_REGEN_SECS, LONGEVITY_REGEN_SECS

        @database_sync_to_async
        def get_regen_candidates():
            from django.db.models import Q, F
            candidates = list(Character.objects.filter(
                is_dying=False,
            ).filter(
                Q(vitality_current__lt=F('vitality_max')) |
                Q(longevity_current__lt=F('longevity_max'))
            ).select_related(
                'current_room__area', 'current_room__zone',
                'origin',
            ))
            result = []
            for char in candidates:
                if not char.combat_sessions.filter(is_active=True).exists():
                    result.append(char)
            return result

        @database_sync_to_async
        def save_regen(char, fields):
            char.save(update_fields=fields)

        regen_candidates = await get_regen_candidates()

        for character in regen_candidates:
            changed_fields = []

            if character.vitality_current < character.vitality_max:
                heal = math.ceil(
                    (character.vitality_max - character.vitality_current) / VITALITY_REGEN_SECS
                )
                character.vitality_current = min(
                    character.vitality_current + heal, character.vitality_max
                )
                changed_fields.append('vitality_current')

            if character.longevity_current < character.longevity_max:
                heal = math.ceil(
                    (character.longevity_max - character.longevity_current) / LONGEVITY_REGEN_SECS
                )
                character.longevity_current = min(
                    character.longevity_current + heal, character.longevity_max
                )
                changed_fields.append('longevity_current')

            if changed_fields:
                await save_regen(character, changed_fields)
                await self.send_to_player(
                    character.pk, '', 'status', await self._build_status_async(character)
                )

    # ------------------------------------------------------------------
    # Dying lore ladder
    # ------------------------------------------------------------------

    async def process_dying_ladder(self):
        from django.utils import timezone
        from apps.shyland.models import Character

        now = timezone.now()

        @database_sync_to_async
        def get_dying_characters():
            return list(Character.objects.filter(is_dying=True).only('id', 'dying_since'))

        dying = await get_dying_characters()
        current_pks = set()

        for character in dying:
            pk = character.pk
            current_pks.add(pk)
            elapsed = int((now - character.dying_since).total_seconds())

            sent = self._dying_ladder_sent.get(pk)
            if sent is None:
                # First sight of this dying character in this process — seed
                # with every threshold already passed so a late tick or an
                # engine restart mid-window doesn't replay earlier lines.
                sent = {threshold for threshold, _ in DYING_LADDER if threshold <= elapsed}
                self._dying_ladder_sent[pk] = sent

            for threshold, line in DYING_LADDER:
                if threshold <= elapsed and threshold not in sent:
                    sent.add(threshold)
                    await self.send_to_player(pk, line, 'error', None)

        for pk in list(self._dying_ladder_sent.keys()):
            if pk not in current_pks:
                del self._dying_ladder_sent[pk]

    # ------------------------------------------------------------------
    # NPC dialogue delivery (v19 brief 9)
    # ------------------------------------------------------------------

    async def process_dialogue_delivery(self):
        from django.utils import timezone
        now = timezone.now()
        due = await self.get_due_dialogue_responses(now)
        for row in due:
            await self.deliver_dialogue_response(row)

    @database_sync_to_async
    def get_due_dialogue_responses(self, now):
        from apps.shyland.models import PendingDialogueResponse
        return list(
            PendingDialogueResponse.objects.filter(fire_at__lte=now)
            .select_related('npc_instance__definition', 'entry')
            .order_by('fire_at', 'position')
        )

    async def deliver_dialogue_response(self, row):
        # NPC died mid-stagger: the instance is marked dead well before its
        # (much later) respawn-timer cleanup deletes the row, so check
        # liveness explicitly rather than relying on cascade timing alone.
        if not row.npc_instance.is_alive:
            await self.delete_pending_dialogue_response(row.pk)
            return

        response_text = await self.draw_dialogue_response(row.npc_instance_id, row.entry_id)
        if response_text is None:
            await self.delete_pending_dialogue_response(row.pk)
            return

        npc_name = row.npc_instance.definition.name

        if row.position == 1:
            connective = await self.draw_connective('second')
            if connective:
                await self.broadcast_to_room(row.room_id, connective.replace('{name}', npc_name), category='room')
        elif row.position >= 2:
            connective = await self.draw_connective('later')
            if connective:
                await self.broadcast_to_room(row.room_id, connective.replace('{name}', npc_name), category='room')

        await self.broadcast_to_room(row.room_id, f'[say] {npc_name}: {response_text}', category='chat')

        if row.is_final:
            asker_room_id = await self.get_character_current_room_id(row.character_id)
            if asker_room_id != row.room_id:
                departure_line = await self.draw_departure_reaction(
                    row.npc_instance_id, row.npc_instance.definition_id,
                )
                if departure_line:
                    await self.broadcast_to_room(row.room_id, departure_line, category='room')

        await self.delete_pending_dialogue_response(row.pk)

    def _pick_excluding_last(self, npc_instance_pk, responses):
        last_pk = self._last_dialogue_response.get(npc_instance_pk)
        pool = [r for r in responses if r.pk != last_pk] if len(responses) > 1 else responses
        chosen = random.choice(pool)
        self._last_dialogue_response[npc_instance_pk] = chosen.pk
        return chosen.text

    @database_sync_to_async
    def draw_dialogue_response(self, npc_instance_pk, entry_pk):
        from apps.shyland.models import DialogueResponse
        responses = list(DialogueResponse.objects.filter(entry_id=entry_pk))
        if not responses:
            return None
        return self._pick_excluding_last(npc_instance_pk, responses)

    @database_sync_to_async
    def draw_connective(self, position_class):
        from apps.shyland.models import DialogueConnective
        pool = list(DialogueConnective.objects.filter(position_class=position_class))
        return random.choice(pool).template if pool else None

    @database_sync_to_async
    def get_character_current_room_id(self, character_pk):
        from apps.shyland.models import Character
        return Character.objects.filter(pk=character_pk).values_list('current_room_id', flat=True).first()

    @database_sync_to_async
    def draw_departure_reaction(self, npc_instance_pk, npc_definition_pk):
        from apps.shyland.models import DialogueEntry, DialogueResponse
        entry = DialogueEntry.objects.filter(
            npc_definition_id=npc_definition_pk, entry_type=DialogueEntry.ENTRY_DEPARTED,
        ).first()
        if entry is None:
            return None
        responses = list(DialogueResponse.objects.filter(entry=entry))
        if not responses:
            return None
        return self._pick_excluding_last(npc_instance_pk, responses)

    @database_sync_to_async
    def delete_pending_dialogue_response(self, pk):
        from apps.shyland.models import PendingDialogueResponse
        PendingDialogueResponse.objects.filter(pk=pk).delete()

    def _build_status(self, character):
        # v20 brief 4: carries location names+colors (#1) and the
        # combat-membership boolean (#2), mirroring the consumer's
        # _status_payload. Sync-context only — the combat-session lookup
        # is a query; async call sites use _build_status_async.
        room = character.current_room
        zone = room.zone if room else None
        area = room.area if room and room.area_id else None
        return {
            'type': 'status',
            # v20 brief 4 amendment 1 (#71): stats-pane header, verbatim.
            'character_name': character.name,
            'vitality': character.vitality_current,
            'vitality_max': character.vitality_max,
            'acuity': round(character.acuity_current, 2),
            'acuity_baseline': round(character.acuity_baseline, 2),
            'acuity_band_low': round(character.acuity_band_low, 2),
            'acuity_band_high': round(character.acuity_band_high, 2),
            'longevity': character.longevity_current,
            'longevity_max': character.longevity_max,
            'room_name': room.name if room else '',
            'zone_name': zone.name if zone else '',
            'zone_color': zone.theme_color if zone else '#CCCCCC',
            'area_name': area.name if area else None,
            'area_color': area.theme_color if area else None,
            'in_combat': character.combat_sessions.filter(is_active=True).exists(),
        }

    async def _build_status_async(self, character):
        return await database_sync_to_async(self._build_status)(character)

    async def send_to_player(self, character_pk, text, category, status, event=None,
                             fight=None):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        # v20 brief 2 (#32): ts is stamped here, at creation — the status
        # payload is delivered as its own client message, so it carries
        # its own ts too. v20 brief 4 (#2): same for fight-info payloads.
        ts = envelope_ts()
        if status is not None and 'ts' not in status:
            status['ts'] = ts
        if fight is not None and 'ts' not in fight:
            fight['ts'] = ts
        await channel_layer.group_send(
            f'player_{character_pk}',
            {
                'type': 'player_message',
                'text': text,
                'category': category,
                'status': status,
                'fight': fight,
                'event': event,
                'ts': ts,
            }
        )

    async def broadcast_to_room(self, room_id, text, category='room', exclude_pk=None):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'room_{room_id}',
            {
                'type': 'room_message',
                'text': text,
                'category': category,
                'exclude_pk': exclude_pk,
                'ts': envelope_ts(),
            }
        )
