import asyncio

import redis.asyncio as aioredis
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .currency import display_for_zone
from .models import Character, ItemInstance, Room, RoomVisit

SLOT_ORDER = [
    'HEAD', 'NECK', 'SHOULDERS', 'CHEST', 'HANDS', 'WAIST',
    'LEGS', 'FEET', 'RING', 'MAIN_HAND', 'OFF_HAND', 'RANGED', 'BACK',
]
SLOT_RANK = {s: i for i, s in enumerate(SLOT_ORDER)}

RARITY_RANK = {
    'common': 1, 'uncommon': 2, 'rare': 3,
    'epic': 4, 'legendary': 5, 'artifact': 6,
}


DIRECTIONS = {
    'north': 'exit_north', 'n': 'exit_north',
    'south': 'exit_south', 's': 'exit_south',
    'east': 'exit_east',  'e': 'exit_east',
    'west': 'exit_west',  'w': 'exit_west',
    'up': 'exit_up',      'u': 'exit_up',
    'down': 'exit_down',  'd': 'exit_down',
}


def _item_suffix(item, defn):
    if defn.item_type == 'bag':
        return f'   — +{defn.carry_bonus} carry capacity'
    if defn.takes_durability_loss:
        if item.is_broken:
            return '   — BROKEN'
        return f'   — {int(round(item.durability_current))}% durability'
    return ''


class SkylandConsumer(AsyncJsonWebsocketConsumer):

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return

        self.character = await self.get_character(user)
        if self.character is None:
            await self.accept()
            await self.output('No character found. Create one to play.', 'error')
            await self.close()
            return

        self.character_pk = self.character.pk
        await self.accept()

        if self.character.current_room_id is None:
            await self.output('You are not in any room. Contact an admin.', 'error')
            return

        room = await self.get_current_room()
        self.room_group = f'room_{room.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        self.redis = aioredis.from_url("redis://redis:6379")
        await self.redis.set(
            f"shyland:online:{self.character_pk}",
            self.character.name,
            ex=90,
        )
        self.heartbeat_task = asyncio.ensure_future(self.presence_heartbeat())

        await self.send_room_description(room)

    async def disconnect(self, code):
        if hasattr(self, 'heartbeat_task'):
            self.heartbeat_task.cancel()
        if hasattr(self, 'character_pk') and hasattr(self, 'redis'):
            await self.redis.delete(f"shyland:online:{self.character_pk}")
        if hasattr(self, 'room_group'):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
        if hasattr(self, 'character'):
            await self.touch_last_seen(self.character)

    # ------------------------------------------------------------------
    # Receive / dispatch
    # ------------------------------------------------------------------

    async def receive_json(self, content):
        raw = content.get('text', '').strip()
        if not raw:
            return

        parts = raw.split(None, 1)
        verb = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        if verb in DIRECTIONS:
            await self.cmd_move(verb)
        elif verb == 'look' or verb == 'l':
            await self.cmd_look()
        elif verb == 'say':
            await self.cmd_say(args)
        elif verb == 'who':
            await self.cmd_who()
        elif verb == 'inventory' or verb == 'inv':
            await self.cmd_inventory()
        elif verb == 'help' or verb == '?':
            await self.cmd_help()
        else:
            await self.output("Unknown command. Type 'help' for a list of commands.", 'system')

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def cmd_look(self):
        room = await self.get_current_room()
        await self.send_room_description(room, entering=True)

    async def cmd_move(self, direction):
        exit_field = DIRECTIONS[direction]
        room = await self.get_current_room()
        destination = getattr(room, exit_field)

        if destination is None:
            exits = room.exits()
            await self.send_json({
                'type': 'output',
                'category': 'error',
                'text': 'There is no exit in that direction.',
                'hint_exits': ', '.join(exits.keys()) if exits else 'none',
            })
            return

        char_name = self.character.name

        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': f'{char_name} has left.',
            'category': 'system',
            'exclude': self.channel_name,
        })
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

        await self.move_character(destination)
        self.room_group = f'room_{destination.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': f'{char_name} has arrived.',
            'category': 'system',
            'exclude': self.channel_name,
        })

        # Re-fetch with full select_related (destination from exit FK lacks area pre-fetch)
        destination = await self.get_current_room()
        await self.send_room_description(destination, entering=True)

    async def cmd_say(self, text):
        if not text:
            await self.output('Say what?', 'system')
            return
        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': f'[say] {self.character.name}: {text}',
            'category': 'chat',
        })

    async def cmd_who(self):
        keys = await self.redis.keys("shyland:online:*")
        if not keys:
            await self.output("No players are currently online.", "system")
            return
        names = await self.redis.mget(*keys)
        online = sorted(n.decode() for n in names if n)
        count = len(online)
        lines = [f"Players online ({count}):"] + [f"  {name}" for name in online]
        await self.output("\n".join(lines), "system")

    async def presence_heartbeat(self):
        while True:
            await asyncio.sleep(60)
            await self.redis.expire(
                f"shyland:online:{self.character_pk}",
                90,
            )

    async def cmd_inventory(self):
        items = await self.get_inventory()
        char = self.character

        equipped = [i for i in items if i.is_equipped]
        unequipped = [i for i in items if not i.is_equipped]

        bag_bonus = sum(
            i.definition.carry_bonus for i in equipped if i.definition.item_type == 'bag'
        )
        max_carry = char.stat_str * 10 + bag_bonus
        current_carry = len(unequipped)

        lines = []

        if equipped:
            lines.append('Equipment:')
            for item in sorted(equipped, key=lambda i: SLOT_RANK.get(i.equipped_slot, 99)):
                defn = item.definition
                name_str = f'{item.rarity.capitalize()} {defn.name} Mk {item.mk_tier}'
                suffix = _item_suffix(item, defn)
                lines.append(f'  [{item.equipped_slot}]  {name_str}{suffix}')
            lines.append('')

        lines.append(f'Inventory ({current_carry}/{max_carry} items):')

        unequipped_sorted = sorted(unequipped, key=lambda i: (
            i.definition.item_type,
            i.mk_tier,
            RARITY_RANK.get(i.rarity, 0),
            i.definition.name,
        ))

        idx = 0
        while idx < len(unequipped_sorted):
            item = unequipped_sorted[idx]
            defn = item.definition
            rarity_label = item.rarity.capitalize()
            name_str = f'{defn.name} Mk {item.mk_tier}'

            if defn.item_type == 'consumable':
                count = 1
                j = idx + 1
                while j < len(unequipped_sorted):
                    other = unequipped_sorted[j]
                    if (other.definition_id == item.definition_id
                            and other.mk_tier == item.mk_tier
                            and other.rarity == item.rarity):
                        count += 1
                        j += 1
                    else:
                        break
                count_str = f'   x{count}' if count > 1 else ''
                lines.append(f'  {rarity_label:<9} {name_str}{count_str}')
                idx = j
            else:
                suffix = _item_suffix(item, defn)
                lines.append(f'  {rarity_label:<9} {name_str}{suffix}')
                idx += 1

        await self.output('\n'.join(lines), 'system')

    async def cmd_help(self):
        room = await self.get_current_room()
        exits = room.exits()
        abbrevs = {'north': 'n', 'south': 's', 'east': 'e', 'west': 'w', 'up': 'u', 'down': 'd'}
        dir_list = ', '.join(f'{d} ({abbrevs[d]})' for d in abbrevs if d in exits)
        movement = dir_list if dir_list else 'none'
        help_text = (
            f'Movement: {movement}\n'
            '\n'
            'Commands:\n'
            '  look / l        — describe this room\n'
            '  say <text>      — speak to players here\n'
            '  who             — list players online\n'
            '  inventory / inv — show carried items and equipment\n'
            '  help / ?        — show this list'
        )
        await self.output(help_text, 'system')

    # ------------------------------------------------------------------
    # Channel layer event handlers
    # ------------------------------------------------------------------

    async def room_message(self, event):
        if event.get('exclude') == self.channel_name:
            return
        await self.output(event['text'], event.get('category', 'system'))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def format_wallet(self, character):
        zone_slug = character.current_room.zone.slug if character.current_room_id else None
        return display_for_zone(character.copper, zone_slug)

    async def output(self, text, category='system'):
        await self.send_json({'type': 'output', 'text': text, 'category': category})

    async def send_room_description(self, room, entering=False):
        char = self.character
        exits = room.exits()
        exit_str = ', '.join(exits.keys()) if exits else 'none'
        others = await self.get_others_in_room(room)

        if room.area:
            location_header = f'[ {room.area.name} — {room.name} ]'
        else:
            location_header = f'[ {room.name} ]'

        area_context = ''
        if room.area and room.area.area_description:
            area_context = f'{room.area.area_description}\n\n'

        text = (
            f'{location_header}\n'
            f'{area_context}'
            f'{room.description}'
        )

        await self.send_json({
            'type': 'output',
            'category': 'room',
            'enter': entering,
            'text': text,
            'players': ', '.join(others) if others else None,
            'exits': exit_str,
        })

        v = char.vitality_current
        a = char.acuity_current
        l = char.longevity_current
        await self.send_json({
            'type': 'status',
            'vitality': v,
            'acuity': a,
            'longevity': l,
            'room_name': room.name,
            'area_name': room.area.name if room.area else None,
        })

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_character(self, user):
        try:
            char = (
                Character.objects
                .select_related('current_room__zone', 'recall_room', 'user__profile')
                .get(user=user)
            )
            return char
        except Character.DoesNotExist:
            return None

    @database_sync_to_async
    def get_current_room(self):
        return (
            Room.objects
            .select_related('zone', 'area',
                            'exit_north', 'exit_south',
                            'exit_east', 'exit_west',
                            'exit_up', 'exit_down')
            .get(pk=self.character.current_room_id)
        )

    @database_sync_to_async
    def move_character(self, destination):
        Character.objects.filter(pk=self.character.pk).update(current_room=destination)
        self.character.current_room = destination
        self.character.current_room_id = destination.pk
        RoomVisit.objects.get_or_create(character=self.character, room=destination)

    @database_sync_to_async
    def touch_last_seen(self, character):
        Character.objects.filter(pk=character.pk).update(last_seen=timezone.now())

    @database_sync_to_async
    def get_inventory(self):
        return list(
            ItemInstance.objects.filter(owner=self.character)
            .select_related('definition')
            .order_by('is_equipped', 'definition__item_type', 'mk_tier', 'rarity', 'definition__name')
        )

    @database_sync_to_async
    def get_others_in_room(self, room):
        chars = list(
            Character.objects
            .filter(current_room=room)
            .exclude(pk=self.character.pk)
            .select_related('user__profile')
        )
        return [c.name for c in chars]

