import asyncio
import json
import random
import uuid

import redis.asyncio as aioredis
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.urls import reverse
from django.utils import timezone

from . import currency
from .currency import display_for_zone
from .item_utils import (
    format_slot_name, generate_item_instance, get_display_name,
    get_display_name_with_tier, get_display_description, get_repair_cost,
    get_repair_success_chance, get_sale_price, parse_item_noun,
    parse_corpse_noun, STAT_LABELS,
)
from .models import (
    Character, CombatSession, ItemInstance,
    NpcInstance, Room, RoomVisit, TravelMessage, TravelNode, VendorEntry,
    COMBAT_ROUND_TICKS, FLEE_COOLDOWN_TICKS,
)

SLOT_ORDER = [
    'HEAD', 'NECK', 'SHOULDERS', 'CHEST', 'HANDS', 'WAIST',
    'LEGS', 'FEET', 'RING', 'MAIN_HAND', 'OFF_HAND', 'RANGED', 'BACK',
]
SLOT_RANK = {s: i for i, s in enumerate(SLOT_ORDER)}

# RING is the only slot a character has two of.
SLOT_CAPACITY = {'RING': 2}

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

DIRECTION_CANONICAL = {
    'north': 'north', 'n': 'north',
    'south': 'south', 's': 'south',
    'east': 'east',   'e': 'east',
    'west': 'west',   'w': 'west',
    'up': 'up',       'u': 'up',
    'down': 'down',   'd': 'down',
}

REVERSE_DIRECTIONS = {
    'north': 'south', 'south': 'north',
    'east': 'west',   'west': 'east',
    'up': 'down',     'down': 'up',
}

_NO_EXIT_DEFAULTS = {
    'north': "There is no exit in that direction.",
    'south': "There is no exit in that direction.",
    'east':  "There is no exit in that direction.",
    'west':  "There is no exit in that direction.",
    'up':    "There is nothing above you.",
    'down':  "You'd have to dig to go that way.",
}


def _join_owned_names(items, conj):
    names = [f'your {get_display_name(i)}' for i in items]
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f'{names[0]} {conj} {names[1]}'
    return ', '.join(names[:-1]) + f', {conj} {names[-1]}'


def _item_suffix(item, defn):
    if defn.item_type == 'bag':
        return f'   — +{defn.carry_bonus} carry capacity'
    if defn.takes_durability_loss:
        if item.is_broken:
            return '   — BROKEN'
        return f'   — {int(round(item.durability_current))}% durability'
    return ''


ORDINALS = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth']


def npc_display_name(npc, npcs_in_room):
    """'the black bear' when unique in the room, 'the second black bear'
    when multiple NPCs share the definition name. Positional: index within
    the same-name NPCs in room parse order (the order parse_npc_noun uses).
    Not a stable per-instance number — it shifts as same-name NPCs die."""
    name = npc.definition.name
    same_name = [n for n in npcs_in_room if n.definition.name == name]
    if len(same_name) <= 1:
        return f"the {name}"
    index = next((i for i, n in enumerate(same_name) if n.pk == npc.pk), None)
    if index is None or index >= len(ORDINALS):
        return f"the {name}"
    return f"the {ORDINALS[index]} {name}"


def parse_presence_name(raw: bytes) -> str:
    """Extract the character name from a presence value.
    Tolerates legacy values that are a bare name string."""
    text = raw.decode()
    try:
        return json.loads(text)["name"]
    except (ValueError, KeyError, TypeError):
        return text


# Guarded heartbeat: self-heals a missing key, refreshes TTL only if this
# session still owns the key, and never clobbers a different session's value.
PRESENCE_HEARTBEAT_LUA = """
local v = redis.call('GET', KEYS[1])
if v == false then
  redis.call('SET', KEYS[1], ARGV[1], 'EX', 90)
  return 1
elseif v == ARGV[1] then
  redis.call('EXPIRE', KEYS[1], 90)
  return 1
else
  return 0
end
"""

# Guarded delete: only removes the key if it still holds this session's value.
PRESENCE_DELETE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
else
  return 0
end
"""


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
            # Structured signal so the client can route to the creator instead
            # of sitting on a dead socket.
            await self.send_json({'type': 'redirect', 'url': reverse('shyland:create_character')})
            await self.close()
            return

        self.character_pk = self.character.pk
        self.last_direction = None
        self._character_is_dying = self.character.is_dying
        await self.accept()

        if self.character.current_room_id is None:
            await self.output('You are not in any room. Contact an admin.', 'error')
            return

        room = await self.get_current_room()
        self.room_group = f'room_{room.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        self.player_group = f'player_{self.character_pk}'
        await self.channel_layer.group_add(self.player_group, self.channel_name)

        self.redis = aioredis.from_url("redis://redis:6379")
        self.session_token = uuid.uuid4().hex
        self.presence_value = json.dumps({
            "name": self.character.name,
            "token": self.session_token,
        })
        await self.redis.set(
            f"shyland:online:{self.character_pk}",
            self.presence_value,
            ex=90,
        )
        self.heartbeat_task = asyncio.ensure_future(self.presence_heartbeat())

        await self.send_room_description(room)

    async def disconnect(self, code):
        if hasattr(self, 'heartbeat_task'):
            self.heartbeat_task.cancel()
        if hasattr(self, 'character_pk') and hasattr(self, 'redis'):
            await self.redis.eval(
                PRESENCE_DELETE_LUA,
                1,
                f"shyland:online:{self.character_pk}",
                self.presence_value,
            )
        if hasattr(self, 'player_group'):
            await self.channel_layer.group_discard(self.player_group, self.channel_name)
        if hasattr(self, 'room_group'):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
        if getattr(self, 'character', None) is not None:
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

        if self._character_is_dying and verb not in ('use',):
            await self.send_output(
                "You are dying! Use a revival item or wait for another player to revive you.",
                'error',
            )
            return

        if verb in DIRECTIONS:
            await self.cmd_move(verb)
        elif verb in ('look', 'l'):
            await self.cmd_look()
        elif verb == 'say':
            await self.cmd_say(args)
        elif verb == 'who':
            await self.cmd_who()
        elif verb in ('inventory', 'inv'):
            await self.cmd_inventory()
        elif verb == 'wallet':
            await self.cmd_wallet()
        elif verb in ('pickup', 'p'):
            await self.cmd_pickup(args)
        elif verb == 'drop':
            await self.cmd_drop(args)
        elif verb in ('equip', 'eq'):
            await self.cmd_equip(args)
        elif verb in ('unequip', 'uneq'):
            await self.cmd_unequip(args)
        elif verb == 'use':
            await self.cmd_use(args)
        elif verb in ('examine', 'ex'):
            await self.cmd_examine(args)
        elif verb == 'loot':
            await self.cmd_loot(args)
        elif verb == 'list':
            await self.cmd_list()
        elif verb == 'buy':
            await self.cmd_buy(args)
        elif verb == 'sell':
            await self.cmd_sell(args)
        elif verb == 'repair':
            await self.cmd_repair(args)
        elif verb in ('kill', 'attack', 'k'):
            await self.cmd_attack(args)
        elif verb == 'flee':
            await self.cmd_flee()
        elif verb == 'travel':
            await self.cmd_travel(args)
        elif verb == 'brief':
            await self.cmd_brief(args)
        elif verb == 'spend':
            await self.cmd_spend(args)
        elif verb == 'stats':
            await self.cmd_stats()
        elif verb in ('help', '?'):
            await self.cmd_help()
        else:
            await self.output("Unknown command. Type 'help' for a list of commands.", 'system')

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def cmd_look(self):
        room = await self.get_current_room()
        await self.send_room_description(room, entering=True, force_long=True)

    async def cmd_move(self, direction):
        exit_field = DIRECTIONS[direction]
        room = await self.get_current_room()
        destination = getattr(room, exit_field)

        if destination is None:
            exits = room.exits()
            canonical = DIRECTION_CANONICAL[direction]
            custom_msg = getattr(room, f'no_exit_{canonical}_msg', '')
            msg = custom_msg if custom_msg else _NO_EXIT_DEFAULTS[canonical]
            await self.send_json({
                'type': 'output',
                'category': 'error',
                'text': msg,
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
        self.last_direction = DIRECTION_CANONICAL[direction]
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

        aggro_npcs = await self.get_aggro_npcs_in_room(destination)
        if aggro_npcs:
            for npc in aggro_npcs:
                await self.send_output(f"A {npc.definition.name} snarls and moves to attack!", 'combat')
            await self.start_combat(aggro_npcs, first_attacker='npc')
        else:
            await self.send_room_description(destination, entering=True)

    async def cmd_travel(self, args):
        room = await self.get_current_room()
        node = await self.get_travel_node(room)

        if node is None:
            await self.output(
                'There is no obelisk here. Travel is a gift of the obelisks — '
                'you must stand before one.', 'error',
            )
            return
        if node.node_type != 'obelisk':
            await self.output(
                'The obelisks project their protection here, but only an obelisk '
                'itself can send you onward.', 'error',
            )
            return

        destinations = await self.get_revealed_destinations(node)

        if not args:
            if not destinations:
                await self.output(
                    'The Obelisk is silent. It has nothing to show you yet — '
                    'the network reveals itself only to those who walk it.', 'system',
                )
                return
            lines = ['The Obelisk offers passage to:']
            for dest in destinations:
                suffix = ' (obelisk)' if dest.node_type == 'obelisk' else ''
                lines.append(f'  {dest.travel_name}{suffix}')
            await self.output('\n'.join(lines), 'system')
            return

        query = args.strip().lower()
        matches = [d for d in destinations if self._travel_name_matches(d.travel_name, query)]

        if not matches:
            await self.output(
                'The Obelisk knows no such place — or you have not yet stood there. '
                'Type "travel" to see where it can send you.', 'error',
            )
            return
        if len(matches) > 1:
            names = ', '.join(d.travel_name for d in matches)
            await self.output(
                f'The Obelisk offers more than one such passage: {names}. '
                'Be more specific.', 'system',
            )
            return

        destination = matches[0].room
        char_name = self.character.name

        departure = await self.get_random_travel_message('departure')
        if departure:
            await self.broadcast_to_room_exclude(departure.replace('{name}', char_name), 'room')

        await self.channel_layer.group_discard(self.room_group, self.channel_name)
        await self.move_character(destination)
        self.last_direction = None
        self.room_group = f'room_{destination.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        traveler = await self.get_random_travel_message('traveler')
        if traveler:
            await self.output(traveler, 'room')

        # Re-fetch with full select_related, same as normal movement.
        destination = await self.get_current_room()
        await self.send_room_description(destination, entering=True)

        arrival = await self.get_random_travel_message('arrival')
        if arrival:
            await self.broadcast_to_room_exclude(arrival.replace('{name}', char_name), 'room')

    @staticmethod
    def _travel_name_matches(travel_name, query):
        """Case-insensitive prefix match, tolerating a leading 'The ' on the node name."""
        name = travel_name.lower()
        if name.startswith(query):
            return True
        return name.startswith('the ') and name[4:].startswith(query)

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
        online = sorted(parse_presence_name(n) for n in names if n)
        count = len(online)
        lines = [f"Players online ({count}):"] + [f"  {name}" for name in online]
        await self.output("\n".join(lines), "system")

    async def presence_heartbeat(self):
        while True:
            await asyncio.sleep(60)
            await self.redis.eval(
                PRESENCE_HEARTBEAT_LUA,
                1,
                f"shyland:online:{self.character_pk}",
                self.presence_value,
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
                if item.is_identified:
                    name_str = f'{item.rarity.capitalize()} {get_display_name_with_tier(item)}'
                else:
                    name_str = get_display_name(item)
                suffix = _item_suffix(item, defn)
                bind_tag = '[bound]' if item.is_soulbound else '[drop]'
                lines.append(f'  [{item.equipped_slot}]  {name_str}{suffix}  {bind_tag}')
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
            bind_tag = '[bound]' if item.is_soulbound else '[drop]'

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
                if item.is_identified:
                    rarity_label = item.rarity.capitalize()
                    name_str = get_display_name_with_tier(item)
                    lines.append(f'  {rarity_label:<9} {name_str}{count_str}  {bind_tag}')
                else:
                    name_str = get_display_name(item)
                    lines.append(f'             {name_str}{count_str}  {bind_tag}')
                idx = j
            else:
                suffix = _item_suffix(item, defn)
                if item.is_identified:
                    rarity_label = item.rarity.capitalize()
                    name_str = get_display_name_with_tier(item)
                    lines.append(f'  {rarity_label:<9} {name_str}{suffix}  {bind_tag}')
                else:
                    name_str = get_display_name(item)
                    lines.append(f'             {name_str}  {bind_tag}')
                idx += 1

        wallet_char = await self.get_character_fresh()
        lines.append('')
        lines.append('Wallet:')
        lines.append(f'  {self.format_wallet(wallet_char)}')

        await self.output('\n'.join(lines), 'system')

    async def cmd_wallet(self):
        char = await self.get_character_fresh()
        await self.output(f'Wallet: {self.format_wallet(char)}', 'system')

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
            '  look / l                   — describe this room\n'
            '  say <text>                 — speak to players here\n'
            '  who                        — list players online\n'
            '  inventory / inv            — show carried items and equipment\n'
            '  wallet                     — show your copper\n'
            '  pickup (p) <item>          — pick up an item from the room\n'
            '  drop <item>                — drop a carried item (unbound items only)\n'
            '  equip (eq) <item>          — equip a carried item\n'
            '  unequip (uneq) <item>      — unequip an equipped item\n'
            '  use <item>                 — use a consumable\n'
            '  examine (ex) <item>        — inspect an item, NPC, or corpse in detail\n'
            '  loot [corpse] [item]       — loot a corpse; bare \'loot\' takes everything from your most recent kill\n'
            '  travel [destination]       — fast-travel via the Obelisk Network (from an obelisk)\n'
            '  list                       — see what a vendor here has for sale\n'
            '  buy <item>                 — buy an item from a vendor here\n'
            '  sell <item>                — sell an unequipped item to a vendor here\n'
            '  repair [item | all]        — pay a mender here to repair damaged gear\n'
            '  kill / attack (k) [npc]    — attack an NPC; bare attack strikes back at whatever hit you first\n'
            '  flee                       — attempt to escape from combat\n'
            '  stats                      — show your character stats and XP\n'
            '  spend <stat> <amount>      — spend stat points (e.g. spend dex 2)\n'
            '  help / ?                   — show this list\n'
            '\n'
            "Item syntax: 'sword' = first sword, '2.sword' = second sword, 'all' = everything (where supported)"
        )
        await self.output(help_text, 'system')

    async def cmd_pickup(self, args):
        if not args:
            await self.output("Pick up what? (look to see what's here)", 'system')
            return

        char = self.character
        room = await self.get_current_room()
        room_items = await self.get_room_items(room)

        noun_result, matched = parse_item_noun(args, room_items)

        if noun_result == 'not_found':
            await self.output("You don't see that here.", 'system')
            return
        if noun_result == 'bad_index':
            await self.output("There aren't that many of those here.", 'system')
            return

        items_to_pick_up = room_items if noun_result == 'all' else [matched]
        current_count, max_capacity = await self.get_carry_capacity(char)

        for item in items_to_pick_up:
            if current_count >= max_capacity:
                await self.output(
                    f"You can't carry any more. ({current_count}/{max_capacity} items)",
                    'system',
                )
                break

            display_name = get_display_name(item)
            await self.transfer_to_character(item, char)
            current_count += 1

            await self.output(f"You pick up {display_name}.", 'system')
            await self.channel_layer.group_send(self.room_group, {
                'type': 'room_message',
                'text': f'{char.name} picks up {display_name}.',
                'category': 'room',
                'exclude': self.channel_name,
            })

    async def cmd_drop(self, args):
        if not args:
            await self.output("Drop what?", 'system')
            return

        char = self.character
        room = await self.get_current_room()
        carried_items = await self.get_carried_items(char)

        noun_result, matched = parse_item_noun(args, carried_items)

        if noun_result == 'not_found':
            await self.output("You aren't carrying that.", 'system')
            return
        if noun_result == 'bad_index':
            await self.output("You don't have that many of those.", 'system')
            return

        items_to_drop = carried_items if noun_result == 'all' else [matched]

        for item in items_to_drop:
            display_name = get_display_name(item)
            if item.is_equipped:
                await self.output(
                    f"You'll need to unequip your {display_name} before dropping it.",
                    'system',
                )
                continue
            if item.is_soulbound:
                await self.output(
                    f"Your {display_name} is bound to you and cannot be dropped.",
                    'system',
                )
                continue

            await self.transfer_to_room(item, room)

            await self.output(f"You drop {display_name}.", 'system')
            await self.channel_layer.group_send(self.room_group, {
                'type': 'room_message',
                'text': f'{char.name} drops {display_name}.',
                'category': 'room',
                'exclude': self.channel_name,
            })

    async def cmd_equip(self, args):
        if not args:
            await self.output("Equip what?", 'system')
            return

        char = self.character
        unequipped_items = await self.get_carried_unequipped_items(char)

        noun_result, matched = parse_item_noun(args, unequipped_items)

        if noun_result == 'not_found':
            await self.output("You aren't carrying that.", 'system')
            return
        if noun_result == 'bad_index':
            await self.output("You don't have that many of those.", 'system')
            return
        if noun_result == 'all':
            await self.output("You can't equip everything at once.", 'system')
            return

        item = matched
        defn = item.definition

        if not defn.valid_slots:
            await self.output("That item cannot be equipped.", 'system')
            return

        equipped_items = await self.get_equipped_items(char)

        # One candidate per way the item could go on: (slot, items displaced).
        # A two-handed item claims both hands from any slot it occupies; a
        # one-handed item going into a hand conflicts with any equipped
        # two-handed item, wherever that item sits (including RANGED).
        candidates = []
        for slot in defn.valid_slots:
            occupants = [i for i in equipped_items if i.equipped_slot == slot]
            capacity = SLOT_CAPACITY.get(slot, 1)

            if defn.is_two_handed:
                extras = [
                    i for i in equipped_items
                    if i.equipped_slot in ('MAIN_HAND', 'OFF_HAND')
                    or i.definition.is_two_handed
                ]
            elif slot in ('MAIN_HAND', 'OFF_HAND'):
                extras = [i for i in equipped_items if i.definition.is_two_handed]
            else:
                extras = []

            base_sets = [[]] if len(occupants) < capacity else [[o] for o in occupants]
            for base in base_sets:
                displaced, seen = [], set()
                for equipped in base + extras:
                    if equipped.pk not in seen:
                        seen.add(equipped.pk)
                        displaced.append(equipped)
                candidates.append((slot, displaced))

        # A slot the item can occupy without displacing anything wins outright.
        free = next(((slot, d) for slot, d in candidates if not d), None)
        if free is not None:
            target_slot = free[0]
            await self.equip_item(item, target_slot, char)
            await self.output(
                f"You equip {get_display_name(item)} in your {format_slot_name(target_slot)}.",
                'system',
            )
            return

        min_size = min(len(d) for _, d in candidates)
        minimal = [(slot, d) for slot, d in candidates if len(d) == min_size]

        if min_size >= 2:
            _, displaced = minimal[0]
            await self.output(
                f"You'd have to unequip {_join_owned_names(displaced, 'and')} first.",
                'system',
            )
            return

        # Exactly one item must come off. If different candidate slots would
        # displace different items, the choice is the player's — refuse.
        distinct, seen = [], set()
        for _, d in minimal:
            if d[0].pk not in seen:
                seen.add(d[0].pk)
                distinct.append(d[0])

        if len(distinct) > 1:
            if all(slot == 'RING' for slot, _ in minimal):
                msg = (
                    f"Both ring slots are full — "
                    f"unequip {_join_owned_names(distinct, 'or')} first."
                )
            else:
                msg = f"You'd have to unequip {_join_owned_names(distinct, 'or')} first."
            await self.output(msg, 'system')
            return

        # Unambiguous one-for-one exchange: auto-swap, if the displaced item
        # can legally come off. Never perform a partial swap.
        displaced_item = distinct[0]
        target_slot = minimal[0][0]

        unequipped_count = 0
        if displaced_item.definition.item_type == 'bag':
            unequipped_count = await self.count_unequipped_items(char)
        blocked = self._unequip_blocked_reason(displaced_item, equipped_items, unequipped_count)
        if blocked:
            await self.output(blocked, 'system')
            return

        await self.unequip_item(displaced_item)
        await self.equip_item(item, target_slot, char)
        await self.output(
            f"You unequip your {get_display_name(displaced_item)} and equip your "
            f"{get_display_name(item)} in your {format_slot_name(target_slot)}.",
            'system',
        )

    async def cmd_unequip(self, args):
        if not args:
            await self.output("Unequip what?", 'system')
            return

        char = self.character
        equipped_items = await self.get_equipped_items(char)

        noun_result, matched = parse_item_noun(args, equipped_items)

        if noun_result == 'not_found':
            await self.output("You don't have that equipped.", 'system')
            return
        if noun_result == 'bad_index':
            await self.output("You don't have that many of those equipped.", 'system')
            return
        if noun_result == 'all':
            await self.output("You can't unequip everything at once.", 'system')
            return

        item = matched
        display_name = get_display_name(item)

        unequipped_count = 0
        if item.definition.item_type == 'bag':
            unequipped_count = await self.count_unequipped_items(char)
        blocked = self._unequip_blocked_reason(item, equipped_items, unequipped_count)
        if blocked:
            await self.output(blocked, 'system')
            return

        await self.unequip_item(item)
        await self.output(
            f"You unequip your {display_name} and stow it in your inventory.",
            'system',
        )

    def _unequip_blocked_reason(self, item, equipped_items, unequipped_count):
        """Return the refusal message if the item cannot legally be unequipped, else None."""
        if item.is_cursed:
            return f"Your {get_display_name(item)} is cursed and cannot be removed."
        if item.definition.item_type == 'bag':
            other_bag_bonus = sum(
                i.definition.carry_bonus for i in equipped_items
                if i.definition.item_type == 'bag' and i.pk != item.pk
            )
            new_limit = self.character.stat_str * 10 + other_bag_bonus
            if (unequipped_count + 1) > new_limit:
                return f"You're carrying too many items to remove your {get_display_name(item)}."
        return None

    async def cmd_use(self, args):
        if not args:
            await self.output("Use what?", 'system')
            return

        char = self.character
        was_dying = self._character_is_dying
        consumables = await self.get_carried_consumables(char)

        noun_result, matched = parse_item_noun(args, consumables)

        if noun_result == 'not_found':
            await self.output("You aren't carrying that.", 'system')
            return
        if noun_result == 'bad_index':
            await self.output("You don't have that many of those.", 'system')
            return
        if noun_result == 'all':
            await self.output("You can't use everything at once.", 'system')
            return

        item = matched
        effect_def = item.definition.effect

        if effect_def is None:
            await self.output("Nothing happens.", 'system')
            return

        mk_tier = item.mk_tier
        msgs = await self.do_apply_effect(effect_def, char, mk_tier)

        await self.consume_item(item)

        for msg in msgs:
            await self.output(msg, 'system')

        room = await self.get_current_room()
        char_fresh = await self.get_character_fresh()

        if was_dying and char_fresh.vitality_current > 0:
            await self.revive_character(char_fresh)
            self._character_is_dying = False
            await self.output(
                "Breath floods back into your lungs. You are alive — barely.", 'system',
            )
            await self.send_room_description(room, entering=False)
            await self.broadcast_to_room_exclude(
                f"{char_fresh.name} staggers back to their feet!", 'combat',
            )
            return

        await self.send_json({
            'type': 'status',
            'vitality': char_fresh.vitality_current,
            'vitality_max': char_fresh.vitality_max,
            'acuity': round(char_fresh.acuity_current, 2),
            'acuity_baseline': round(char_fresh.acuity_baseline, 2),
            'acuity_band_low': round(char_fresh.acuity_band_low, 2),
            'acuity_band_high': round(char_fresh.acuity_band_high, 2),
            'longevity': char_fresh.longevity_current,
            'longevity_max': char_fresh.longevity_max,
            'room_name': room.name,
            'area_name': room.area.name if room.area_id else None,
        })

    def _format_identified_item_lines(self, item):
        defn = item.definition
        lines = []
        lines.append(f'{item.rarity.capitalize()} {get_display_name_with_tier(item)}')
        lines.append(f'  {defn.description}')
        lines.append('')
        lines.append(f'  Type:       {defn.item_type.title()}')
        lines.append(f'  Genre:      {defn.genre_tag.title()}')

        if (defn.item_type == 'weapon'
                and item.damage_midpoint is not None
                and item.damage_spread is not None):
            dmg_lo = int(item.damage_midpoint - item.damage_spread)
            dmg_hi = int(item.damage_midpoint + item.damage_spread)
            lines.append(f'  Damage:     {dmg_lo} – {dmg_hi}')

        if defn.takes_durability_loss:
            dur_str = f'  Durability: {int(item.durability_current)}%'
            if item.is_broken:
                dur_str += ' (BROKEN)'
            lines.append(dur_str)

        if defn.item_type == 'bag':
            lines.append(f'  Carry bonus: +{defn.carry_bonus}')

        if item.rolled_primary_stats:
            lines.append('')
            for entry in item.rolled_primary_stats:
                label = STAT_LABELS.get(entry['stat'], entry['stat'].replace('_', ' ').title())
                lines.append(f'  {label}: {entry["value"]}')

        if item.rolled_secondary_stats:
            if not item.rolled_primary_stats:
                lines.append('')
            for entry in item.rolled_secondary_stats:
                label = STAT_LABELS.get(entry['stat'], entry['stat'].replace('_', ' ').title())
                lines.append(f'  {label}: {entry["value"]}')

        if item.is_equipped:
            lines.append(f'  Equipped:   {format_slot_name(item.equipped_slot)}')

        if item.is_soulbound:
            lines.append('  Bound:      This item is bound to you.')

        if item.is_cursed and item.curse_identified:
            lines.append('  Curse:      This item carries a curse.')

        if not item.is_equipped and not item.is_soulbound:
            lines.append('  Note:       This item is not yet bound — you may drop it.')

        return lines

    async def cmd_examine(self, args):
        if not args:
            await self.output("Examine what?", 'system')
            return

        char = self.character
        room = await self.get_current_room()
        carried_items = await self.get_carried_items(char)
        room_items = await self.get_room_items(room)
        combined = carried_items + room_items

        noun_result, matched = parse_item_noun(args, combined)

        if noun_result == 'all':
            await self.output("You can't examine everything at once.", 'system')
            return
        if noun_result == 'bad_index':
            await self.output("There aren't that many of those.", 'system')
            return

        if noun_result == 'single':
            item = matched
            lines = []
            if not item.is_identified:
                lines.append(get_display_name(item))
                lines.append('')
                lines.append(f'  {get_display_description(item)}')
                lines.append('')
                lines.append('  (You cannot determine anything further about this item.)')
                if item.is_unidentifiable:
                    lines.append('  No known method of identification will reveal its true nature.')
            else:
                lines = self._format_identified_item_lines(item)
            await self.output('\n'.join(lines), 'system')
            return

        # Search live NPCs
        npcs = await self.get_npcs_in_room(room)
        noun_lower = args.strip().lower()
        npc_match = next((n for n in npcs if noun_lower in n.name.lower()), None)

        if npc_match is not None:
            lines = [npc_match.name, '', f'  {npc_match.definition.description}']
            await self.output('\n'.join(lines), 'system')
            return

        # Search corpses
        corpses = await self.get_corpses_in_room(room)
        code, corpse = parse_corpse_noun(args, corpses)

        if code == 'bad_index':
            await self.output("There aren't that many of those.", 'system')
            return

        if code == 'single':
            from .currency import display_for_zone
            zone_slug = room.zone.slug if room.zone_id else None
            lines = [f'The corpse of {corpse.npc_name_snapshot}.']

            if corpse.copper_drop > 0:
                lines.append(f'  Currency:  {display_for_zone(corpse.copper_drop, zone_slug)}')
            else:
                lines.append('  Currency:  No currency.')

            if char.pk == corpse.killed_by_id:
                contents = await self.get_corpse_contents(corpse)
                if contents:
                    lines.append('')
                    for item in contents:
                        lines.append('')
                        lines.extend(self._format_identified_item_lines(item))
                else:
                    lines.append('  No items.')
            else:
                lines.append(
                    '  The body lies here, its belongings just out of reach. Whatever it was\n'
                    "  carrying is none of your business — you didn't make this kill."
                )

            await self.output('\n'.join(lines), 'system')
            return

        await self.output("You don't see that here.", 'system')

    async def cmd_loot(self, args):
        from .currency import display_for_zone

        room = await self.get_current_room()
        character = await self.get_character(self.scope['user'])
        corpses = await self.get_corpses_in_room(room)

        if not corpses:
            await self.output("There is nothing to loot here.", "system")
            return

        arg_parts = args.split(None, 1) if args else []
        target_corpse = None
        item_noun = None

        if not arg_parts:
            target_corpse = corpses[0]
        else:
            first = arg_parts[0]
            rest = arg_parts[1] if len(arg_parts) > 1 else None
            code, matched = parse_corpse_noun(first, corpses)
            if code == 'single':
                target_corpse = matched
                item_noun = rest
            elif code == 'bad_index':
                await self.output("There aren't that many corpses here.", "error")
                return
            else:
                target_corpse = corpses[0]
                item_noun = args.strip()

        if target_corpse.killed_by_id != character.pk:
            await self.output("That is not your kill; you may not loot it.", "error")
            return

        copper_amount = await self.do_loot_copper(target_corpse, character)
        if copper_amount > 0:
            zone_slug = room.zone.slug if room.zone_id else None
            copper_str = display_for_zone(copper_amount, zone_slug)
            await self.output(f"You loot {copper_str} from {target_corpse.display_name}.", "system")

        contents = await self.get_corpse_contents(target_corpse)

        if not contents:
            await self.output(f"{target_corpse.display_name.capitalize()} is already empty.", "system")
            deleted = await self.check_corpse_empty_and_delete(target_corpse)
            if deleted:
                await self.channel_layer.group_send(self.room_group, {
                    'type': 'room_message',
                    'text': f"{target_corpse.display_name.capitalize()} slowly disappears.",
                    'category': 'room',
                })
            return

        if item_noun:
            code, item = parse_item_noun(item_noun, contents)
            if code == 'not_found':
                await self.output("You don't see that here.", "error")
                return
            if code == 'bad_index':
                await self.output("There aren't that many of those.", "error")
                return
            items_to_loot = [item]
        else:
            items_to_loot = contents

        current_count, max_carry = await self.get_carry_counts(character)

        for item in items_to_loot:
            if current_count >= max_carry:
                await self.output(
                    f"You can't carry any more. ({current_count}/{max_carry} items)",
                    "error"
                )
                break
            name = await self.do_loot_item(item, character)
            await self.output(f"You loot {name}.", "system")
            current_count += 1

        deleted = await self.check_corpse_empty_and_delete(target_corpse)
        if deleted:
            await self.channel_layer.group_send(self.room_group, {
                'type': 'room_message',
                'text': f"{target_corpse.display_name.capitalize()} slowly disappears.",
                'category': 'room',
            })

    # ------------------------------------------------------------------
    # Commerce commands
    # ------------------------------------------------------------------

    @staticmethod
    def _entry_exhausted(entry):
        return entry.stock_limit is not None and entry.sold_count >= entry.stock_limit

    @staticmethod
    def _entry_display_name(entry):
        # Vendor entries reference definitions, not instances — format
        # directly rather than via get_display_name_with_tier.
        name = entry.item_definition.name
        if entry.item_definition.suppress_mk_suffix:
            return name
        return f'{name} Mk {entry.mk_tier}'

    async def cmd_list(self):
        room = await self.get_current_room()
        vendor = await self.get_vendor_in_room(room)
        if vendor is None:
            await self.output('There is no one here to trade with.', 'error')
            return

        entries = await self.get_vendor_entries(vendor)
        listable = [e for e in entries if not self._entry_exhausted(e)]
        if not listable:
            await self.output(f'{vendor.name} has nothing left for sale.', 'system')
            return

        lines = [f'{vendor.name} offers:']
        for entry in listable:
            line = f'  {self._entry_display_name(entry)} — {entry.price} copper'
            if entry.stock_limit is not None:
                line += f' ({entry.stock_limit - entry.sold_count} left)'
            lines.append(line)
        await self.output('\n'.join(lines), 'system')

    async def cmd_buy(self, args):
        room = await self.get_current_room()
        vendor = await self.get_vendor_in_room(room)
        if vendor is None:
            await self.output('There is no one here to trade with.', 'error')
            return

        if not args:
            await self.output('Buy what?', 'system')
            return

        entries = await self.get_vendor_entries(vendor)
        query = args.strip().lower()
        entry = next(
            (e for e in entries if e.item_definition.name.lower().startswith(query)),
            None,
        )
        if entry is None:
            await self.output("They don't sell that.", 'system')
            return
        if self._entry_exhausted(entry):
            await self.output('Sold out.', 'system')
            return

        char = await self.get_character_fresh()
        if entry.price > char.copper:
            await self.output(
                f"You can't afford that — it costs {entry.price} copper.", 'system',
            )
            return

        current_count, max_capacity = await self.get_carry_capacity(char)
        if current_count >= max_capacity:
            await self.output(
                f"You can't carry any more. ({current_count}/{max_capacity} items)",
                'system',
            )
            return

        result = await self.do_buy(entry, char)
        if result == 'poor':
            await self.output(
                f"You can't afford that — it costs {entry.price} copper.", 'system',
            )
            return
        if result == 'sold_out':
            await self.output('Sold out.', 'system')
            return
        await self.output(
            f'You buy {get_display_name_with_tier(result)} for {entry.price} copper.',
            'system',
        )

    async def cmd_sell(self, args):
        room = await self.get_current_room()
        vendor = await self.get_vendor_in_room(room)
        if vendor is None:
            await self.output('There is no one here to trade with.', 'error')
            return

        if not args:
            await self.output('Sell what?', 'system')
            return

        char = self.character
        carried = await self.get_carried_items(char)
        query = args.strip().lower()
        matches = [i for i in carried if get_display_name(i).lower().startswith(query)]
        if not matches:
            await self.output("You aren't carrying that.", 'system')
            return

        unequipped = [i for i in matches if not i.is_equipped]
        if not unequipped:
            await self.output("You'll have to unequip it first.", 'system')
            return

        item = unequipped[0]
        name = get_display_name_with_tier(item)
        price = await self.do_sell(item, char)
        await self.output(f'You sell {name} for {price} copper.', 'system')

    async def cmd_repair(self, args):
        char = await self.get_character_fresh()
        room = await self.get_current_room()
        repairer = await self.get_repairer_in_room(room)
        if repairer is None:
            await self.output('There is no one here who can repair.', 'error')
            return

        arg = args.strip().lower() if args else ''
        damaged = await self.get_damaged_items(char)

        if arg == 'all':
            if not damaged:
                await self.output('You have nothing to repair.', 'system')
                return
            lines = []
            repaired = failed = spent = 0
            for item in damaged:
                name = get_display_name_with_tier(item)
                outcome, cost = await self.do_repair_attempt(item, char)
                if outcome == 'poor':
                    lines.append(
                        f"You can't afford to repair {name} ({cost} copper) — "
                        'you stop there.'
                    )
                    break
                spent += cost
                if outcome == 'success':
                    repaired += 1
                    lines.append(f'{name} is restored to full condition. ({cost} copper)')
                else:
                    failed += 1
                    lines.append(f"The mending on {name} didn't take. ({cost} copper)")
            lines.append(
                f'Repaired {repaired} item{"s" if repaired != 1 else ""}, '
                f'{failed} attempt{"s" if failed != 1 else ""} failed, '
                f'{spent} copper spent.'
            )
            await self.output('\n'.join(lines), 'system')
            return

        if arg:
            items = await self.get_carried_items(char)
            matches = [i for i in items if get_display_name(i).lower().startswith(arg)]
            if not matches:
                await self.output("You aren't carrying that.", 'system')
                return
            item = matches[0]
            if (not item.definition.takes_durability_loss
                    or item.durability_current >= 100.0):
                await self.output("That doesn't need repair.", 'system')
                return
        else:
            if not damaged:
                await self.output('You have nothing to repair.', 'system')
                return
            item = damaged[0]

        name = get_display_name_with_tier(item)
        outcome, cost = await self.do_repair_attempt(item, char)
        if outcome == 'poor':
            await self.output(
                f"Repairing your {name} costs {cost} copper — you can't afford it.",
                'system',
            )
        elif outcome == 'success':
            await self.output(
                f'{repairer.name} restores your {name} to full condition. '
                f'({cost} copper)', 'system',
            )
        else:
            await self.output(
                f"{repairer.name} works on your {name}, but the mending didn't "
                f'take. ({cost} copper)', 'system',
            )

    # ------------------------------------------------------------------
    # Combat commands
    # ------------------------------------------------------------------

    async def cmd_attack(self, args):
        character = await self.get_character_fresh()
        room = await self.get_current_room()
        npcs_in_room = await self.get_live_npcs_in_room(room)

        if not args:
            # Targetless attack only auto-targets under aggro: the
            # earliest-engaged living NPC in the active combat session.
            npc = await self.get_first_attacker_npc(character)
            if npc is None:
                await self.send_output("Attack what?", 'error')
                return
        else:
            npc = await self.parse_npc_noun(args, npcs_in_room)

            if npc is None:
                await self.send_output("You don't see that here.", 'error')
                return

        display = npc_display_name(npc, npcs_in_room)

        session = await self.get_active_combat_session(character)
        if session and await self.npc_in_session(session, npc):
            await self.send_output(f"You're already fighting {display}.", 'combat')
            return

        await self.send_output(f"You move to attack {display}!", 'combat')
        await self.broadcast_to_room_exclude(
            f"{character.name} moves to attack the {npc.definition.name}!", 'combat'
        )
        await self.start_combat([npc], first_attacker='character')

    async def cmd_flee(self):
        character = await self.get_character_fresh()

        session = await self.get_active_combat_session(character)
        if not session:
            await self.send_output("You are not in combat.", 'error')
            return

        if character.is_dying:
            await self.send_output("You are too close to death to flee!", 'error')
            return

        on_cooldown = await self.check_flee_cooldown(character, session)
        if on_cooldown:
            await self.send_output("You are still recovering from your last flee attempt.", 'error')
            return

        npcs = await self.get_session_npcs(session)
        if not npcs:
            await self.end_combat_session(session)
            return

        avg_per = sum(
            npc.definition.base_per * npc.definition.scaling_factor * npc.mk_tier
            for npc in npcs
        ) / len(npcs)

        success = (character.stat_dex + random.randint(1, 20)) > avg_per

        if success:
            result = await self.get_flee_destination(character)
            if result is None:
                await self.send_output("There is nowhere to run!", 'error')
                await self.record_flee_attempt(character, session)
                return

            destination, flee_dir = result
            await self.send_output("You have successfully fled from your enemies.", 'combat')
            await self.broadcast_to_room_exclude(
                f"{character.name} fled the room leaving the enemies looking confused.", 'combat'
            )
            await self.end_combat_session(session)
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            await self.move_character(destination)
            self.last_direction = flee_dir
            self.room_group = f"room_{destination.id}"
            await self.channel_layer.group_add(self.room_group, self.channel_name)

            aggro_npcs = await self.get_aggro_npcs_in_room(destination)
            if aggro_npcs:
                for npc in aggro_npcs:
                    await self.send_output(f"A {npc.definition.name} snarls and moves to attack!", 'combat')
                await self.start_combat(aggro_npcs, first_attacker='npc')
            else:
                destination_full = await self.get_current_room()
                await self.send_room_description(destination_full, entering=True)
        else:
            await self.send_output("You tried to flee but your enemies are too strong.", 'combat')
            await self.broadcast_to_room_exclude(
                f"{character.name} tried to flee combat but could not slip away.", 'combat'
            )
            await self.record_flee_attempt(character, session)

    # ------------------------------------------------------------------
    # Stat commands
    # ------------------------------------------------------------------

    async def cmd_stats(self):
        character = await self.get_character_fresh()
        await self._send_stats(character)

    async def _send_stats(self, character):
        from .combat_utils import xp_for_next_level
        lines = [
            f"[ Character Stats — {character.name} (Level {character.level}) ]",
            f"  Strength     (STR): {character.stat_str}",
            f"  Dexterity    (DEX): {character.stat_dex}",
            f"  Endurance    (END): {character.stat_end}",
            f"  Intelligence (INT): {character.stat_int}",
            f"  Wisdom       (WIS): {character.stat_wis}",
            f"  Perception   (PER): {character.stat_per}",
            f"",
            f"  Vitality:   {character.vitality_current} / {character.vitality_max}",
            f"  Longevity:  {character.longevity_current} / {character.longevity_max}",
            f"  Acuity:     {character.acuity_current:.1f} (baseline {character.acuity_baseline:.1f})",
            f"",
            f"  XP: {character.xp} / {xp_for_next_level(character.level)} (next level)",
            f"  Unspent stat points: {character.unspent_stat_points}",
        ]
        if character.unspent_stat_points > 0:
            lines.append(f"  Type 'spend <stat> <amount>' to allocate. (e.g. 'spend str 2')")
        await self.send_output('\n'.join(lines), 'system')

    async def cmd_spend(self, args):
        VALID_STATS = {
            'str': 'Strength',
            'dex': 'Dexterity',
            'end': 'Endurance',
            'int': 'Intelligence',
            'wis': 'Wisdom',
            'per': 'Perception',
        }

        character = await self.get_character_fresh()

        if not args:
            await self._send_stats(character)
            return

        parts = args.lower().split()
        if len(parts) != 2:
            await self.send_output(
                "Usage: spend <stat> <amount>  (e.g. 'spend dex 2')  |  "
                "Valid stats: str dex end int wis per", 'error'
            )
            return

        stat_name, amount_str = parts

        if stat_name not in VALID_STATS:
            await self.send_output(
                f"Unknown stat '{stat_name}'. Valid stats: {', '.join(VALID_STATS.keys())}", 'error'
            )
            return

        try:
            amount = int(amount_str)
        except ValueError:
            await self.send_output(f"'{amount_str}' is not a valid number.", 'error')
            return

        if amount <= 0:
            await self.send_output("Amount must be greater than zero.", 'error')
            return

        if character.unspent_stat_points <= 0:
            await self.send_output("You have no unspent stat points.", 'error')
            return

        if amount > character.unspent_stat_points:
            pts = character.unspent_stat_points
            await self.send_output(
                f"You only have {pts} unspent stat point{'s' if pts != 1 else ''}.", 'error'
            )
            return

        @database_sync_to_async
        def apply_spend(char, stat, pts):
            from .combat_utils import recalculate_bars
            attr = f'stat_{stat}'
            current = getattr(char, attr)
            setattr(char, attr, current + pts)
            char.unspent_stat_points -= pts
            if stat in ('end', 'str', 'wis'):
                recalculate_bars(char)
                char.save(update_fields=[
                    attr, 'unspent_stat_points',
                    'vitality_max', 'vitality_current',
                    'longevity_max', 'longevity_current',
                ])
            else:
                char.save(update_fields=[attr, 'unspent_stat_points'])
            return getattr(char, attr)

        new_value = await apply_spend(character, stat_name, amount)
        remaining = character.unspent_stat_points

        await self.send_output(
            f"{VALID_STATS[stat_name]} increased to {new_value}. "
            f"{'No' if remaining == 0 else remaining} stat point{'s' if remaining != 1 else ''} remaining.",
            'system'
        )

        room = character.current_room
        await self.send_json({
            'type': 'status',
            'vitality': character.vitality_current,
            'vitality_max': character.vitality_max,
            'acuity': round(character.acuity_current, 2),
            'acuity_baseline': round(character.acuity_baseline, 2),
            'acuity_band_low': round(character.acuity_band_low, 2),
            'acuity_band_high': round(character.acuity_band_high, 2),
            'longevity': character.longevity_current,
            'longevity_max': character.longevity_max,
            'room_name': room.name if room else '',
            'area_name': room.area.name if room and room.area_id else None,
        })

    async def cmd_brief(self, args):
        arg = args.strip().lower() if args else ''
        if arg not in ('on', 'off'):
            await self.send_output('Usage: brief on | brief off', category='error')
            return
        value = (arg == 'on')
        await self._set_brief_mode(value)
        self.character.brief_mode = value
        state = 'on' if value else 'off'
        await self.send_output(f'Brief mode is now {state}.', category='system')

    # ------------------------------------------------------------------
    # Channel layer event handlers
    # ------------------------------------------------------------------

    async def room_message(self, event):
        if event.get('exclude') == self.channel_name:
            return
        exclude_pk = event.get('exclude_pk')
        if exclude_pk is not None and exclude_pk == self.character_pk:
            return
        await self.output(event['text'], event.get('category', 'system'))

    async def player_message(self, event):
        """Handle messages sent directly to this player (e.g. effect ticks from tick engine)."""
        event_type = event.get('event')
        if event_type == 'clear':
            await self.send_json({'type': 'clear'})
        if event.get('text'):
            await self.send_json({
                'type': 'output',
                'text': event['text'],
                'category': event.get('category', 'system'),
            })
        if event.get('status') is not None:
            await self.send_json(event['status'])

        if event_type == 'dying':
            self._character_is_dying = True
        elif event_type == 'respawn':
            char = await self.get_character_fresh()
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            self.room_group = f'room_{char.current_room_id}'
            await self.channel_layer.group_add(self.room_group, self.channel_name)
            self.last_direction = None
            room = await self.get_current_room()
            await self.send_room_description(room, entering=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def send_output(self, text, category='system'):
        await self.send_json({'type': 'output', 'text': text, 'category': category})

    async def broadcast_to_room_exclude(self, text, category='room'):
        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': text,
            'category': category,
            'exclude': self.channel_name,
        })

    def format_wallet(self, character):
        zone_slug = character.current_room.zone.slug if character.current_room_id else None
        return display_for_zone(character.copper, zone_slug)

    async def output(self, text, category='system'):
        await self.send_json({'type': 'output', 'text': text, 'category': category})

    async def send_room_description(self, room, entering=False, force_long=False):
        char = await self.get_character_fresh()
        exits = room.exits()
        exit_str = ', '.join(exits.keys()) if exits else 'none'
        others_db = await self.get_others_in_room(room)
        # Filter to only characters who are actively connected (have a Redis presence key)
        online_names = set()
        if others_db:
            keys = await self.redis.keys("shyland:online:*")
            if keys:
                values = await self.redis.mget(*keys)
                online_names = {parse_presence_name(v) for v in values if v}
        others = [name for name in others_db if name in online_names]
        npcs = await self.get_npcs_in_room(room)
        corpses = await self.get_corpses_in_room(room)

        if room.area:
            location_header = f'[ {room.area.name} — {room.name} ]'
        else:
            location_header = f'[ {room.name} ]'

        area_context = ''
        if room.area and room.area.area_description:
            area_context = f'{room.area.area_description}\n\n'

        if force_long:
            description_text = room.description
            await self._record_visit(char, room)
        else:
            show_brief = await self._check_and_record_visit(char, room)
            description_text = room.brief_description if show_brief else room.description

        text = (
            f'{location_header}\n'
            f'{area_context}'
            f'{description_text}'
        )

        await self.send_json({
            'type': 'output',
            'category': 'room',
            'enter': entering,
            'text': text,
            'players': ', '.join(others) if others else None,
            'exits': exit_str,
        })

        for npc in npcs:
            await self.output(f"{npc.name} is here.", 'room')

        for corpse in corpses:
            await self.output(f"The corpse of {corpse.npc_name_snapshot} lies here.", 'room')

        await self.send_json({
            'type': 'status',
            'vitality': char.vitality_current,
            'vitality_max': char.vitality_max,
            'acuity': round(char.acuity_current, 2),
            'acuity_baseline': round(char.acuity_baseline, 2),
            'acuity_band_low': round(char.acuity_band_low, 2),
            'acuity_band_high': round(char.acuity_band_high, 2),
            'longevity': char.longevity_current,
            'longevity_max': char.longevity_max,
            'room_name': room.name,
            'area_name': room.area.name if room.area_id else None,
        })

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_character(self, user):
        try:
            char = (
                Character.objects
                .select_related(
                    'current_room__zone', 'recall_room',
                    'archetype__unarmed_message_pool',
                )
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

    @database_sync_to_async
    def touch_last_seen(self, character):
        Character.objects.filter(pk=character.pk).update(last_seen=timezone.now())

    @database_sync_to_async
    def _set_brief_mode(self, value):
        Character.objects.filter(pk=self.character_pk).update(brief_mode=value)

    @database_sync_to_async
    def get_travel_node(self, room):
        return TravelNode.objects.filter(room=room).first()

    @database_sync_to_async
    def get_revealed_destinations(self, current_node):
        return list(
            TravelNode.objects
            .filter(room__visits__character_id=self.character_pk)
            .exclude(pk=current_node.pk)
            .select_related('room')
            .order_by('travel_name')
        )

    @database_sync_to_async
    def get_random_travel_message(self, category):
        texts = list(
            TravelMessage.objects.filter(category=category)
            .values_list('text', flat=True)
        )
        return random.choice(texts) if texts else None

    @database_sync_to_async
    def _check_and_record_visit(self, character, room):
        _, created = RoomVisit.objects.get_or_create(character=character, room=room)
        if character.brief_mode:
            return True
        return not created

    @database_sync_to_async
    def _record_visit(self, character, room):
        RoomVisit.objects.get_or_create(character=character, room=room)

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
        )
        return [c.name for c in chars]

    @database_sync_to_async
    def get_room_items(self, room):
        return list(
            ItemInstance.objects.filter(current_room=room, owner__isnull=True, corpse__isnull=True)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_carried_items(self, character):
        return list(
            ItemInstance.objects.filter(owner=character)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_carried_unequipped_items(self, character):
        return list(
            ItemInstance.objects.filter(owner=character, is_equipped=False)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_equipped_items(self, character):
        return list(
            ItemInstance.objects.filter(owner=character, is_equipped=True)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_carried_consumables(self, character):
        return list(
            ItemInstance.objects.filter(
                owner=character,
                is_equipped=False,
                definition__item_type='consumable',
            )
            .select_related('definition', 'definition__effect')
        )

    @database_sync_to_async
    def get_carry_capacity(self, character):
        from django.db.models import Sum
        items = ItemInstance.objects.filter(owner=character)
        current_count = items.count()
        bag_bonus = items.filter(
            is_equipped=True,
            definition__item_type='bag',
        ).aggregate(total=Sum('definition__carry_bonus'))['total'] or 0
        max_capacity = character.stat_str * 10 + bag_bonus
        return (current_count, max_capacity)

    @database_sync_to_async
    def count_unequipped_items(self, character):
        return ItemInstance.objects.filter(owner=character, is_equipped=False).count()

    @database_sync_to_async
    def transfer_to_character(self, item, character):
        item.owner = character
        item.current_room = None
        item.save()

    @database_sync_to_async
    def transfer_to_room(self, item, room):
        item.current_room = room
        item.owner = None
        if not item.is_unidentifiable:
            item.is_identified = False
        item.save()

    @database_sync_to_async
    def equip_item(self, item, slot, character):
        item.is_equipped = True
        item.equipped_slot = slot
        item.is_soulbound = True
        item.soulbound_to = character
        item.save()

    @database_sync_to_async
    def unequip_item(self, item):
        item.is_equipped = False
        item.equipped_slot = ''
        item.save()

    @database_sync_to_async
    def apply_character_stat_change(self, character):
        character.save()

    @database_sync_to_async
    def do_apply_effect(self, effect_def, character, mk_tier):
        from .effect_utils import apply_effect_definition
        return apply_effect_definition(effect_def, character, mk_tier, removed_by_label='consumable')

    @database_sync_to_async
    def consume_item(self, item):
        item.delete()

    @database_sync_to_async
    def get_npcs_in_room(self, room):
        from .models import NpcInstance
        return list(
            NpcInstance.objects.filter(current_room=room, is_alive=True)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_corpses_in_room(self, room):
        from .models import Corpse
        return list(
            Corpse.objects.filter(current_room=room)
            .select_related('killed_by', 'npc_definition')
            .prefetch_related('contents__definition')
            .order_by('-created_at')
        )

    @database_sync_to_async
    def get_corpse_contents(self, corpse):
        return list(corpse.contents.select_related('definition').all())

    @database_sync_to_async
    def do_loot_item(self, item, character):
        name = get_display_name(item)
        item.corpse = None
        item.owner = character
        item.save()
        return name

    @database_sync_to_async
    def do_loot_copper(self, corpse, character):
        from django.db.models import F
        amount = corpse.copper_drop
        if amount > 0:
            Character.objects.filter(pk=character.pk).update(copper=F('copper') + amount)
            corpse.copper_drop = 0
            corpse.save(update_fields=['copper_drop'])
        return amount

    @database_sync_to_async
    def check_corpse_empty_and_delete(self, corpse):
        if not corpse.contents.exists():
            corpse.delete()
            return True
        return False

    @database_sync_to_async
    def get_carry_counts(self, character):
        current = ItemInstance.objects.filter(owner=character, is_equipped=False).count()
        equipped_bags = list(
            ItemInstance.objects.filter(
                owner=character, is_equipped=True, definition__item_type='bag'
            ).select_related('definition')
        )
        bag_bonus = sum(b.definition.carry_bonus for b in equipped_bags)
        max_carry = character.stat_str * 10 + bag_bonus
        return current, max_carry

    # ------------------------------------------------------------------
    # Commerce DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_vendor_in_room(self, room):
        """First living NPC in the room whose definition has an active VendorEntry."""
        return (
            NpcInstance.objects.filter(
                current_room=room,
                is_alive=True,
                definition__vendor_entries__is_active=True,
            )
            .select_related('definition')
            .order_by('pk')
            .distinct()
            .first()
        )

    @database_sync_to_async
    def get_repairer_in_room(self, room):
        return (
            NpcInstance.objects.filter(
                current_room=room,
                is_alive=True,
                definition__is_repairer=True,
            )
            .select_related('definition')
            .order_by('pk')
            .first()
        )

    @database_sync_to_async
    def get_vendor_entries(self, vendor):
        """Active entries for a vendor, exhausted ones included (buy reports Sold out)."""
        return list(
            VendorEntry.objects.filter(
                npc_definition_id=vendor.definition_id, is_active=True,
            )
            .select_related('item_definition')
            .order_by('item_definition__name', 'mk_tier')
        )

    @database_sync_to_async
    def do_buy(self, entry, character):
        """Atomically charge, count the sale, and create the purchased item."""
        from django.db import transaction
        with transaction.atomic():
            fresh = VendorEntry.objects.select_related('item_definition').select_for_update().get(pk=entry.pk)
            if fresh.stock_limit is not None and fresh.sold_count >= fresh.stock_limit:
                return 'sold_out'
            char = Character.objects.select_for_update().get(pk=character.pk)
            try:
                char.copper = currency.subtract(char.copper, fresh.price)
            except ValueError:
                return 'poor'
            char.save(update_fields=['copper'])
            fresh.sold_count += 1
            fresh.save(update_fields=['sold_count'])
            item = generate_item_instance(
                definition=fresh.item_definition,
                mk_tier=fresh.mk_tier,
                rarity='common',
                owner=char,
            )
            item.save()
        self.character.copper = char.copper
        return item

    @database_sync_to_async
    def do_sell(self, item, character):
        """Credit the sale price and delete the sold instance — compensated disposal."""
        from django.db import transaction
        price = get_sale_price(item)
        with transaction.atomic():
            char = Character.objects.select_for_update().get(pk=character.pk)
            char.copper = currency.add(char.copper, price)
            char.save(update_fields=['copper'])
            item.delete()
        self.character.copper = char.copper
        return price

    @database_sync_to_async
    def get_damaged_items(self, character):
        """Eligible repair targets, most-damaged first (stable tie-break on pk)."""
        return list(
            ItemInstance.objects.filter(
                owner=character,
                definition__takes_durability_loss=True,
                durability_current__lt=100.0,
            )
            .select_related('definition')
            .order_by('durability_current', 'pk')
        )

    @database_sync_to_async
    def do_repair_attempt(self, item, character):
        """One paid repair attempt. Returns (outcome, cost); outcome is
        'poor' (refused, nothing charged), 'success', or 'fail' (copper spent,
        item unchanged)."""
        from django.db import transaction
        cost = get_repair_cost(item)
        with transaction.atomic():
            char = Character.objects.select_for_update().get(pk=character.pk)
            try:
                char.copper = currency.subtract(char.copper, cost)
            except ValueError:
                return ('poor', cost)
            char.save(update_fields=['copper'])
            if random.random() < get_repair_success_chance(item):
                item.durability_current = 100.0
                item.is_broken = False
                item.save(update_fields=['durability_current', 'is_broken'])
                outcome = 'success'
            else:
                outcome = 'fail'
        self.character.copper = char.copper
        return (outcome, cost)

    # ------------------------------------------------------------------
    # Combat DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_character_fresh(self):
        char = Character.objects.select_related(
            'current_room__zone', 'current_room__area', 'recall_room',
            'archetype__unarmed_message_pool',
        ).get(pk=self.character_pk)
        self.character = char
        self._character_is_dying = char.is_dying
        return char

    @database_sync_to_async
    def revive_character(self, character):
        character.is_dying = False
        character.dying_since = None
        character.save(update_fields=['is_dying', 'dying_since'])

    @database_sync_to_async
    def get_aggro_npcs_in_room(self, room):
        return list(NpcInstance.objects.filter(
            current_room=room,
            is_alive=True,
            definition__is_aggressive=True,
        ).select_related('definition').prefetch_related('definition__effects__effect_definition'))

    @database_sync_to_async
    def get_live_npcs_in_room(self, room):
        return list(NpcInstance.objects.filter(
            current_room=room,
            is_alive=True,
        ).select_related('definition').prefetch_related('definition__effects__effect_definition'))

    @database_sync_to_async
    def parse_npc_noun(self, noun_str, npcs):
        noun_str = noun_str.strip().lower()
        index = 1
        keyword = noun_str
        if '.' in noun_str:
            parts = noun_str.split('.', 1)
            if parts[0].isdigit():
                index = int(parts[0])
                keyword = parts[1]
        matches = [n for n in npcs if keyword in n.definition.name.lower()]
        if not matches or index > len(matches):
            return None
        return matches[index - 1]

    @database_sync_to_async
    def start_combat(self, npcs, first_attacker='character'):
        existing = CombatSession.objects.filter(
            is_active=True,
            characters=self.character,
        ).first()
        if existing:
            session = existing
        else:
            session = CombatSession.objects.create(
                room_id=self.character.current_room_id,
                first_attacker=first_attacker,
            )
            session.characters.add(self.character)
        for npc in npcs:
            session.npcs.add(npc)
        session.save()
        return session

    @database_sync_to_async
    def get_active_combat_session(self, character):
        return CombatSession.objects.filter(is_active=True, characters=character).first()

    @database_sync_to_async
    def npc_in_session(self, session, npc):
        return session.npcs.filter(pk=npc.pk).exists()

    @database_sync_to_async
    def get_first_attacker_npc(self, character):
        """Earliest-engaged living NPC in the character's active combat
        session (through-row order = join order), or None without aggro."""
        session = CombatSession.objects.filter(
            is_active=True, characters=character,
        ).first()
        if session is None:
            return None
        link = (
            CombatSession.npcs.through.objects
            .filter(combatsession=session, npcinstance__is_alive=True)
            .select_related('npcinstance__definition')
            .order_by('pk')
            .first()
        )
        return link.npcinstance if link else None

    @database_sync_to_async
    def get_session_npcs(self, session):
        return list(session.npcs.select_related('definition').all())

    @database_sync_to_async
    def end_combat_session(self, session):
        session.is_active = False
        session.save(update_fields=['is_active'])
        session.npcs.clear()

    @database_sync_to_async
    def get_flee_destination(self, character):
        room = Room.objects.select_related(
            'exit_north', 'exit_south', 'exit_east', 'exit_west', 'exit_up', 'exit_down'
        ).get(pk=character.current_room_id)
        exits = room.exits()

        reverse = REVERSE_DIRECTIONS.get(self.last_direction)
        if reverse and reverse in exits:
            destination = getattr(room, f'exit_{reverse}')
            if destination is not None:
                return destination, reverse

        available = list(exits.keys())
        if available:
            direction = random.choice(available)
            destination = getattr(room, f'exit_{direction}')
            if destination is not None:
                return destination, direction

        return None

    @database_sync_to_async
    def check_flee_cooldown(self, character, session):
        from django.utils import timezone
        from datetime import timedelta
        if session.last_flee_attempt_at is None:
            return False
        if session.last_flee_character_id != character.pk:
            return False
        cooldown_secs = FLEE_COOLDOWN_TICKS * COMBAT_ROUND_TICKS
        cutoff = timezone.now() - timedelta(seconds=cooldown_secs)
        return session.last_flee_attempt_at > cutoff

    @database_sync_to_async
    def record_flee_attempt(self, character, session):
        from django.utils import timezone
        session.last_flee_attempt_at = timezone.now()
        session.last_flee_character = character
        session.save(update_fields=['last_flee_attempt_at', 'last_flee_character'])

