from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .currency import display_for_zone
from .models import Character, Room, RoomVisit


DIRECTIONS = {
    'north': 'exit_north', 'n': 'exit_north',
    'south': 'exit_south', 's': 'exit_south',
    'east': 'exit_east',  'e': 'exit_east',
    'west': 'exit_west',  'w': 'exit_west',
    'up': 'exit_up',      'u': 'exit_up',
    'down': 'exit_down',  'd': 'exit_down',
}


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

        await self.accept()

        if self.character.current_room_id is None:
            await self.output('You are not in any room. Contact an admin.', 'error')
            return

        room = await self.get_current_room()
        self.room_group = f'room_{room.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.send_room_description(room)

    async def disconnect(self, code):
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
        else:
            await self.output("Unknown command. Type 'look' to see your surroundings.", 'system')

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def cmd_look(self):
        room = await self.get_current_room()
        await self.send_room_description(room)

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
        names = await self.get_online_names()
        if names:
            listing = '\n'.join(f'  {n}' for n in names)
            await self.output(f'Players online:\n{listing}', 'system')
        else:
            await self.output('No players are online.', 'system')

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

        await self.send_json({
            'type': 'output',
            'category': 'room',
            'enter': entering,
            'text': f'[ {room.name} ]\n{room.description}',
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
            .select_related('zone',
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
    def get_others_in_room(self, room):
        chars = list(
            Character.objects
            .filter(current_room=room)
            .exclude(pk=self.character.pk)
            .select_related('user__profile')
        )
        return [c.name for c in chars]

    @database_sync_to_async
    def get_online_names(self):
        chars = list(Character.objects.select_related('user__profile'))
        return [c.name for c in chars]
