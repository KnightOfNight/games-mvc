import asyncio
import logging

from channels.db import database_sync_to_async
from django.core.management.base import BaseCommand

logger = logging.getLogger('shyland.tick')


class Command(BaseCommand):
    help = 'Run the Shyland tick engine (1-second loop).'

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
            apply_npc_effects, xp_for_kill,
        )
        from apps.shyland.item_utils import create_corpse, get_durability_penalty

        now = timezone.now()

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
            session.is_active = False
            session.save(update_fields=['is_active'])

        stale = await get_stale_sessions()
        for session in stale:
            await close_session(session)
            logger.info(f"Combat session {session.pk} closed (stale)")

        # --- Dying state expiry ---
        @_dsa
        def get_expired_dying():
            cutoff = now - timedelta(seconds=DYING_DURATION_SECS)
            return list(Character.objects.filter(
                is_dying=True,
                dying_since__lte=cutoff,
            ).select_related('recall_room', 'user__profile'))

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
            msg = f"You have died and awakened at {recall.name if recall else 'your recall point'}."
            if broken:
                msg += f" Your {', '.join(broken)} {'has' if len(broken) == 1 else 'have'} broken."
            await self.send_to_player(character.pk, msg, 'system', {
                'type': 'status',
                'vitality': character.vitality_current,
                'acuity': character.acuity_current,
                'longevity': character.longevity_current,
                'room_name': recall.name if recall else '',
                'area_name': None,
            })
            logger.info(f"Character {name} died and respawned at room {recall.pk if recall else 'None'}")

        # --- Active combat sessions ---
        @_dsa
        def get_active_sessions():
            return list(CombatSession.objects.filter(is_active=True).prefetch_related(
                'characters__user__profile',
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
                continue

            @_dsa
            def load_participants(session):
                chars = list(session.characters.select_related('user__profile').all())
                npcs = list(session.npcs.select_related('definition').prefetch_related(
                    'definition__effects__effect_definition'
                ).all())
                return chars, npcs

            characters, npcs = await load_participants(session)

            if not characters or not npcs:
                await close_session(session)
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

            if not player_actions and npcs:
                @_dsa
                def create_auto_attack(session, character, npc):
                    return CombatAction.objects.create(
                        combat_session=session,
                        character=character,
                        action_type=CombatAction.ACTION_ATTACK,
                        target_npc=npc,
                    )
                player_actions = [await create_auto_attack(session, character, npcs[0])]

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
                    CombatAction, ItemInstance, DYING_DURATION_SECS, STAT_POINTS_PER_LEVEL,
                )
                from apps.shyland.combat_utils import (
                    get_npc_stats, resolve_hit, calculate_damage,
                    get_npc_health_description, apply_npc_effects, xp_for_kill,
                    xp_for_next_level, recalculate_bars,
                )
                from apps.shyland.item_utils import get_durability_penalty, create_corpse

                _now = _tz.now()
                messages = []
                statuses = []
                room_messages = []

                focus_npc_pk = npcs[0].pk if npcs else None
                live_npcs = list(npcs)

                for action in ordered_actions:
                    if action.is_processed:
                        continue
                    CombatAction.objects.filter(pk=action.pk).update(is_processed=True)

                    # --- Character attacks NPC ---
                    if action.character_id and action.target_npc_id:
                        npc = next((n for n in live_npcs if n.pk == action.target_npc_id), None)
                        if npc is None or not npc.is_alive:
                            continue

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
                            messages.append((character.pk, f"You miss the {npc.definition.name}.", 'combat'))
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
                        acuity_mod = round(max(0.1, min(1.9, character.acuity_current)), 1)
                        damage = calculate_damage(base_damage, stat_bonus, acuity_mod, dur_mod, hit_result, is_focus_target=is_focus)
                        damage_int = max(1, int(damage))

                        npc.vitality_current = max(0, npc.vitality_current - damage_int)
                        npc.save(update_fields=['vitality_current'])

                        if hit_result == 'critical':
                            msg = f"You land a critical hit on the {npc.definition.name} for {damage_int} damage!"
                        else:
                            msg = f"You hit the {npc.definition.name} for {damage_int} damage."

                        health_desc = get_npc_health_description(npc.vitality_current, npc.vitality_max)
                        msg += f" The {npc.definition.name} {health_desc}."
                        messages.append((character.pk, msg, 'combat'))

                        if npc.vitality_current <= 0:
                            npc.is_alive = False
                            npc_def = npc.definition
                            npc.respawn_at = _now + _td(minutes=npc_def.respawn_minutes)
                            npc.save(update_fields=['is_alive', 'respawn_at'])

                            xp = xp_for_kill(npc, character)
                            character.xp += xp
                            character.save(update_fields=['xp'])

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
                                    'system'
                                ))

                            create_corpse(npc, character)

                            messages.append((character.pk, f"You have slain the {npc.definition.name}! (+{xp} XP)", 'combat'))
                            room_messages.append((session.room_id, f"{character.name} has slain the {npc.definition.name}!", 'combat'))

                            live_npcs = [n for n in live_npcs if n.pk != npc.pk]
                            session.npcs.remove(npc)

                            if not live_npcs:
                                session.is_active = False
                                session.save(update_fields=['is_active'])
                                messages.append((character.pk, "Combat has ended.", 'system'))
                                break

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
                            messages.append((character.pk, f"The {npc.definition.name} misses you.", 'combat'))
                            continue

                        base_damage = _random.uniform(
                            npc_stats['str'] * 0.8,
                            npc_stats['str'] * 1.2,
                        )
                        damage = calculate_damage(base_damage, 0, 1.0, 1.0, hit_result, is_focus_target=True)
                        damage_int = max(1, int(damage))

                        character.vitality_current = max(0, character.vitality_current - damage_int)

                        if hit_result == 'critical':
                            msg = f"The {npc.definition.name} lands a critical hit on you for {damage_int} damage!"
                        else:
                            msg = f"The {npc.definition.name} hits you for {damage_int} damage."

                        effect_msgs = apply_npc_effects(npc, character)
                        if effect_msgs:
                            msg += " " + " and ".join(effect_msgs) + "."

                        messages.append((character.pk, msg, 'combat'))

                        if character.vitality_current <= 0:
                            character.vitality_current = 0
                            character.is_dying = True
                            character.dying_since = _now
                            character.save(update_fields=['vitality_current', 'is_dying', 'dying_since'])
                            messages.append((character.pk,
                                f"You have been brought to the brink of death! You have {DYING_DURATION_SECS} seconds to be revived.",
                                'combat'))
                            room_messages.append((session.room_id,
                                f"{character.name} has fallen and is dying!", 'combat'))
                        else:
                            character.save(update_fields=['vitality_current'])

                        statuses.append((character.pk, {
                            'type': 'status',
                            'vitality': character.vitality_current,
                            'acuity': character.acuity_current,
                            'longevity': character.longevity_current,
                            'room_name': '',
                            'area_name': None,
                        }))

                return messages, statuses, room_messages

            messages, statuses, room_messages = await execute_actions(
                session, ordered_actions, character, npcs
            )

            for char_pk, text, category in messages:
                await self.send_to_player(char_pk, text, category, None)
            for char_pk, status in statuses:
                await self.send_to_player(char_pk, '', 'status', status)
            for room_id, text, category in room_messages:
                await self.broadcast_to_room(room_id, text, category)

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
        due = await self.get_due_respawns(now)

        for npc in due:
            definition = npc.definition
            mk_tier = npc.mk_tier
            room_id = npc.spawn_room_id
            await self.respawn_npc(npc.pk, definition, mk_tier, room_id)
            logger.info(
                f"NPC respawned: {definition.name} (Mk {mk_tier}) in room {room_id}"
            )

    @database_sync_to_async
    def get_due_respawns(self, now):
        from apps.shyland.models import NpcInstance
        return list(
            NpcInstance.objects.filter(
                is_alive=False,
                respawn_at__lte=now,
                definition__is_unique=False,
                spawn_room__isnull=False,
            ).select_related('definition', 'spawn_room')
        )

    @database_sync_to_async
    def respawn_npc(self, dead_pk, definition, mk_tier, room_id):
        from apps.shyland.models import NpcInstance, Room
        NpcInstance.objects.filter(pk=dead_pk).delete()
        room = Room.objects.get(pk=room_id)
        NpcInstance.objects.create(
            definition=definition,
            current_room=room,
            spawn_room=room,
            mk_tier=mk_tier,
            vitality_current=definition.base_vitality,
            vitality_max=definition.base_vitality,
            is_alive=True,
        )

    # ------------------------------------------------------------------
    # Effects: per-tick DoT/HoT, Acuity drift, expiry
    # ------------------------------------------------------------------

    async def process_effects(self, tick_number):
        from django.utils import timezone
        from django.db.models import F
        from apps.shyland.models import (
            EffectInstance, Character,
            COMBAT_ROUND_TICKS, ACUITY_DRIFT_RATE,
        )
        from apps.shyland.combat_utils import apply_stat_effect

        now = timezone.now()
        is_round_boundary = (tick_number % COMBAT_ROUND_TICKS == 0)

        # ---- Phase 1: Per-tick DoT/HoT and Acuity shift (round boundaries only) ----
        if is_round_boundary:
            @database_sync_to_async
            def get_active_ticking_effects():
                return list(EffectInstance.objects.filter(
                    is_active=True,
                    expires_at__isnull=False,
                    expires_at__gt=now,
                    definition__effect_type__in=[
                        'dot_vitality', 'dot_acuity', 'dot_longevity',
                        'shift_acuity_high', 'shift_acuity_low',
                    ],
                ).select_related('definition', 'target__user__profile'))

            @database_sync_to_async
            def save_char_fields(char, fields):
                char.save(update_fields=fields)

            @database_sync_to_async
            def set_dying_state(char):
                from django.utils import timezone as tz
                char.is_dying = True
                char.dying_since = tz.now()
                char.save(update_fields=['is_dying', 'dying_since'])

            ticking_effects = await get_active_ticking_effects()

            for effect in ticking_effects:
                character = effect.target
                effect_type = effect.definition.effect_type
                magnitude = effect.magnitude

                if effect_type == 'dot_vitality':
                    damage = max(1, int(magnitude))
                    character.vitality_current = max(0, character.vitality_current - damage)
                    await save_char_fields(character, ['vitality_current'])
                    msg = f"You take {damage} damage from {effect.definition.name}."
                    await self.send_to_player(
                        character.pk, msg, 'system',
                        {'vitality': character.vitality_current}
                    )
                    if character.vitality_current <= 0:
                        await set_dying_state(character)
                        await self.send_to_player(
                            character.pk,
                            f"The {effect.definition.name} has brought you to the brink of death! "
                            f"You have 30 seconds to be revived.",
                            'combat', None
                        )

                elif effect_type == 'dot_acuity':
                    character.acuity_current = round(
                        max(0.1, min(1.9, character.acuity_current - magnitude)), 1
                    )
                    await save_char_fields(character, ['acuity_current'])
                    msg = f"{effect.definition.name} disrupts your focus."
                    await self.send_to_player(
                        character.pk, msg, 'system',
                        {'acuity': character.acuity_current}
                    )

                elif effect_type == 'dot_longevity':
                    drain = max(1, int(magnitude))
                    character.longevity_current = max(0, character.longevity_current - drain)
                    await save_char_fields(character, ['longevity_current'])
                    msg = f"{effect.definition.name} drains your endurance."
                    await self.send_to_player(
                        character.pk, msg, 'system',
                        {'longevity': character.longevity_current}
                    )

                elif effect_type == 'shift_acuity_high':
                    character.acuity_current = round(
                        min(1.9, character.acuity_current + magnitude), 1
                    )
                    await save_char_fields(character, ['acuity_current'])
                    await self.send_to_player(
                        character.pk, '', 'system', {'acuity': character.acuity_current}
                    )

                elif effect_type == 'shift_acuity_low':
                    character.acuity_current = round(
                        max(0.1, character.acuity_current - magnitude), 1
                    )
                    await save_char_fields(character, ['acuity_current'])
                    await self.send_to_player(
                        character.pk, '', 'system', {'acuity': character.acuity_current}
                    )

        # ---- Phase 2: Passive Acuity drift (every tick) ----
        @database_sync_to_async
        def get_characters_needing_drift():
            candidates = list(Character.objects.exclude(
                acuity_current=F('acuity_baseline')
            ).select_related('user__profile').prefetch_related('active_effects__definition'))

            acuity_effect_types = {'shift_acuity_high', 'shift_acuity_low'}
            result = []
            for char in candidates:
                has_active_acuity_effect = any(
                    e.is_active and e.definition.effect_type in acuity_effect_types
                    for e in char.active_effects.all()
                )
                if not has_active_acuity_effect:
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
            await self.send_to_player(character.pk, '', 'system', {'acuity': new_acuity})

        # ---- Phase 3: Effect expiry (every tick) ----
        @database_sync_to_async
        def get_expired_effects_now():
            return list(EffectInstance.objects.filter(
                is_active=True,
                expires_at__isnull=False,
                expires_at__lte=now,
            ).select_related('definition', 'target__user__profile'))

        @database_sync_to_async
        def expire_and_reverse(effect, char):
            if effect.definition.effect_type in ('stat_bonus', 'stat_penalty'):
                apply_stat_effect(char, effect, reverse=True)
            effect.is_active = False
            effect.removed_by = 'timeout'
            effect.save(update_fields=['is_active', 'removed_by'])

        EXPIRY_MESSAGES = {
            'shift_acuity_high': "Your heightened focus fades. Your mind settles.",
            'shift_acuity_low':  "The fog lifts from your mind. Your thoughts sharpen.",
            'dot_vitality':      "The pain subsides.",
            'dot_acuity':        "The mental static clears.",
            'dot_longevity':     "The draining sensation fades.",
        }
        SILENT_TYPES = {'restore_vitality', 'restore_acuity', 'restore_longevity', 'curse_generic'}

        expired = await get_expired_effects_now()

        for effect in expired:
            character = effect.target
            effect_type = effect.definition.effect_type

            await expire_and_reverse(effect, character)

            if effect_type in SILENT_TYPES:
                logger.info(f"Effect expired (silent): {effect.definition.slug} on {character.name}")
                continue

            if effect_type == 'stat_bonus':
                msg = f"The {effect.definition.name} fades. Your body returns to normal."
            elif effect_type == 'stat_penalty':
                msg = f"The {effect.definition.name} lifts."
            else:
                msg = EXPIRY_MESSAGES.get(effect_type, "An effect has worn off.")

            await self.send_to_player(character.pk, msg, 'system', None)
            logger.info(f"Effect expired: {effect.definition.slug} on {character.name}")

    async def send_to_player(self, character_pk, text, category, status):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'player_{character_pk}',
            {
                'type': 'player_message',
                'text': text,
                'category': category,
                'status': status,
            }
        )

    async def broadcast_to_room(self, room_id, text, category='room'):
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'room_{room_id}',
            {
                'type': 'room_message',
                'text': text,
                'category': category,
            }
        )
