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
        await self.process_corpse_decay()
        await self.process_npc_respawn()
        await self.process_effect_expiry()

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
    # Effect expiry
    # ------------------------------------------------------------------

    async def process_effect_expiry(self):
        from django.utils import timezone
        now = timezone.now()
        expired = await self.get_expired_effects(now)

        for effect in expired:
            character = effect.target
            effect_type = effect.definition.effect_type
            effect_name = effect.definition.name
            char_name = character.name
            slug = effect.definition.slug

            msg = self.get_expiry_message(effect_type, effect_name)
            await self.expire_effect(effect.pk)

            if msg:
                status = await self.get_character_status(character.pk)
                await self.send_to_player(character.pk, msg, 'system', status)
                logger.info(f"Effect expired: {slug} on {char_name}")

    def get_expiry_message(self, effect_type, effect_name):
        messages = {
            'shift_acuity_high': "Your heightened focus fades. Your mind settles.",
            'shift_acuity_low':  "The fog lifts from your mind. Your thoughts sharpen.",
            'dot_vitality':      "The pain subsides.",
            'dot_acuity':        "The mental static clears.",
            'dot_longevity':     "The draining sensation fades.",
            'stat_bonus':        f"The {effect_name} fades. Your body returns to normal.",
            'stat_penalty':      f"The {effect_name} lifts.",
        }
        silent = {'restore_vitality', 'restore_acuity', 'restore_longevity', 'curse_generic'}
        if effect_type in silent:
            return None
        return messages.get(effect_type, "An effect has worn off.")

    @database_sync_to_async
    def get_expired_effects(self, now):
        from apps.shyland.models import EffectInstance
        return list(
            EffectInstance.objects.filter(
                is_active=True,
                expires_at__lte=now,
                expires_at__isnull=False,
            ).select_related(
                'definition',
                'target__user__profile',
                'target__current_room__zone',
                'target__current_room__area',
            )
        )

    @database_sync_to_async
    def expire_effect(self, pk):
        from apps.shyland.models import EffectInstance
        EffectInstance.objects.filter(pk=pk).update(
            is_active=False,
            removed_by='timeout',
        )

    @database_sync_to_async
    def get_character_status(self, character_pk):
        from apps.shyland.models import Character
        char = Character.objects.select_related(
            'current_room__zone', 'current_room__area'
        ).get(pk=character_pk)
        room = char.current_room
        return {
            'type': 'status',
            'vitality':  char.vitality_current,
            'acuity':    char.acuity_current,
            'longevity': char.longevity_current,
            'room_name': room.name if room else '',
            'area_name': room.area.name if room and room.area_id else None,
        }

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
