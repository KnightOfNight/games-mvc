import asyncio
import random

import redis.asyncio as aioredis
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .currency import display_for_zone
from .item_utils import (
    format_slot_name, get_display_name, get_display_description,
    parse_item_noun, parse_corpse_noun, STAT_LABELS,
)
from .models import Character, EffectInstance, ItemInstance, Room, RoomVisit

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

        self.player_group = f'player_{self.character_pk}'
        await self.channel_layer.group_add(self.player_group, self.channel_name)

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
        if hasattr(self, 'player_group'):
            await self.channel_layer.group_discard(self.player_group, self.channel_name)
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
        elif verb in ('look', 'l'):
            await self.cmd_look()
        elif verb == 'say':
            await self.cmd_say(args)
        elif verb == 'who':
            await self.cmd_who()
        elif verb in ('inventory', 'inv'):
            await self.cmd_inventory()
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
        elif verb in ('help', '?'):
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
                if item.is_identified:
                    name_str = f'{item.rarity.capitalize()} {get_display_name(item)} Mk {item.mk_tier}'
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
                    name_str = f'{get_display_name(item)} Mk {item.mk_tier}'
                    lines.append(f'  {rarity_label:<9} {name_str}{count_str}  {bind_tag}')
                else:
                    name_str = get_display_name(item)
                    lines.append(f'             {name_str}{count_str}  {bind_tag}')
                idx = j
            else:
                suffix = _item_suffix(item, defn)
                if item.is_identified:
                    rarity_label = item.rarity.capitalize()
                    name_str = f'{get_display_name(item)} Mk {item.mk_tier}'
                    lines.append(f'  {rarity_label:<9} {name_str}{suffix}  {bind_tag}')
                else:
                    name_str = get_display_name(item)
                    lines.append(f'             {name_str}  {bind_tag}')
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
            '  look / l                   — describe this room\n'
            '  say <text>                 — speak to players here\n'
            '  who                        — list players online\n'
            '  inventory / inv            — show carried items and equipment\n'
            '  pickup (p) <item>          — pick up an item from the room\n'
            '  drop <item>                — drop a carried item (unbound items only)\n'
            '  equip (eq) <item>          — equip a carried item\n'
            '  unequip (uneq) <item>      — unequip an equipped item\n'
            '  use <item>                 — use a consumable\n'
            '  examine (ex) <item>        — inspect an item, NPC, or corpse in detail\n'
            '  loot [corpse] [item]       — loot a corpse; bare \'loot\' takes everything from your most recent kill\n'
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
        equipped_by_slot = {i.equipped_slot: i for i in equipped_items}
        occupied_slots = set(equipped_by_slot.keys())

        if defn.is_two_handed:
            main_item = equipped_by_slot.get('MAIN_HAND')
            off_item = equipped_by_slot.get('OFF_HAND')

            if main_item and off_item:
                msg = (
                    f"Your Main Hand ({get_display_name(main_item)}) and "
                    f"Off Hand ({get_display_name(off_item)}) slots are both occupied. "
                    f"Unequip them first."
                )
                await self.output(msg, 'system')
                return
            elif main_item:
                await self.output(
                    f"Your Main Hand slot is occupied by your {get_display_name(main_item)}. "
                    f"Unequip it first.",
                    'system',
                )
                return
            elif off_item:
                await self.output(
                    f"Your Off Hand slot is occupied by your {get_display_name(off_item)}. "
                    f"Unequip it first.",
                    'system',
                )
                return

            target_slot = defn.valid_slots[0]
        else:
            target_slot = None
            for slot in defn.valid_slots:
                if slot not in occupied_slots:
                    target_slot = slot
                    break

            if target_slot is None:
                first_slot = defn.valid_slots[0]
                blocking = equipped_by_slot.get(first_slot)
                if blocking:
                    msg = (
                        f"Your {format_slot_name(first_slot)} slot is occupied by your "
                        f"{get_display_name(blocking)}. Unequip it first."
                    )
                else:
                    msg = f"No suitable slot available for that item."
                await self.output(msg, 'system')
                return

        await self.equip_item(item, target_slot, char)
        display_name = get_display_name(item)
        await self.output(
            f"You equip {display_name} in your {format_slot_name(target_slot)}.",
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
        defn = item.definition
        display_name = get_display_name(item)

        if item.is_cursed:
            await self.output(f"Your {display_name} is cursed and cannot be removed.", 'system')
            return

        if defn.item_type == 'bag':
            other_bag_bonus = sum(
                i.definition.carry_bonus for i in equipped_items
                if i.definition.item_type == 'bag' and i.pk != item.pk
            )
            new_limit = char.stat_str * 10 + other_bag_bonus
            unequipped_count = await self.count_unequipped_items(char)
            if (unequipped_count + 1) > new_limit:
                await self.output(
                    f"You're carrying too many items to remove your {display_name}.",
                    'system',
                )
                return

        await self.unequip_item(item)
        await self.output(
            f"You unequip your {display_name} and stow it in your inventory.",
            'system',
        )

    async def cmd_use(self, args):
        if not args:
            await self.output("Use what?", 'system')
            return

        char = self.character
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

        if effect_def.effect_type == 'durability_restore':
            await self.output(
                "You attempt a repair, but the repair system isn't implemented yet.",
                'system',
            )
            return

        magnitude = random.uniform(effect_def.magnitude_min, effect_def.magnitude_max)

        has_duration = (
            effect_def.duration_min is not None and effect_def.duration_max is not None
        )
        duration = (
            random.uniform(effect_def.duration_min, effect_def.duration_max)
            if has_duration else None
        )

        effect_type = effect_def.effect_type
        stat_changed = False

        if effect_type == 'restore_vitality':
            char.vitality_current = min(
                char.vitality_current + magnitude, char.vitality_max
            )
            await self.apply_character_stat_change(char)
            stat_changed = True
            msg = f"You feel your wounds closing. (+{round(magnitude)} vitality)"
        elif effect_type == 'restore_acuity':
            char.acuity_current = min(char.acuity_current + magnitude, 100)
            await self.apply_character_stat_change(char)
            stat_changed = True
            msg = f"Your thoughts sharpen and settle. (+{round(magnitude)} acuity)"
        elif effect_type == 'restore_longevity':
            char.longevity_current = min(
                char.longevity_current + magnitude, char.longevity_max
            )
            await self.apply_character_stat_change(char)
            stat_changed = True
            msg = f"A wave of renewed endurance washes over you. (+{round(magnitude)} longevity)"
        elif effect_type == 'shift_acuity_high':
            char.acuity_current = min(char.acuity_current + magnitude, 100)
            await self.apply_character_stat_change(char)
            stat_changed = True
            msg = f"Your senses narrow to a razor edge. (+{round(magnitude)} acuity)"
        elif effect_type == 'shift_acuity_low':
            char.acuity_current = max(char.acuity_current - magnitude, 0)
            await self.apply_character_stat_change(char)
            stat_changed = True
            msg = f"Your mind diffuses, thoughts spreading wide. (-{round(magnitude)} acuity)"
        else:
            msg = "You feel a strange effect take hold."

        if duration is not None:
            await self.create_effect_instance(effect_def, char, item, magnitude, duration)

        await self.consume_item(item)
        await self.output(msg, 'system')

        if stat_changed:
            room = await self.get_current_room()
            await self.send_json({
                'type': 'status',
                'vitality': char.vitality_current,
                'acuity': char.acuity_current,
                'longevity': char.longevity_current,
                'room_name': room.name,
                'area_name': room.area.name if room.area else None,
            })

    def _format_identified_item_lines(self, item):
        defn = item.definition
        lines = []
        lines.append(f'{item.rarity.capitalize()} {get_display_name(item)} Mk {item.mk_tier}')
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
    # Channel layer event handlers
    # ------------------------------------------------------------------

    async def room_message(self, event):
        if event.get('exclude') == self.channel_name:
            return
        await self.output(event['text'], event.get('category', 'system'))

    async def player_message(self, event):
        """Handle messages sent directly to this player (e.g. effect expiry from tick engine)."""
        await self.send_json({
            'type': 'output',
            'text': event['text'],
            'category': event.get('category', 'system'),
        })
        if 'status' in event:
            await self.send_json(event['status'])

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
        npcs = await self.get_npcs_in_room(room)
        corpses = await self.get_corpses_in_room(room)

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

        for npc in npcs:
            await self.output(f"{npc.name} is here.", 'room')

        for corpse in corpses:
            await self.output(f"The corpse of {corpse.npc_name_snapshot} lies here.", 'room')

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
    def create_effect_instance(self, effect_def, character, item, magnitude, duration):
        from datetime import timedelta
        from django.utils import timezone
        expires = timezone.now() + timedelta(seconds=duration) if duration else None
        return EffectInstance.objects.create(
            definition=effect_def,
            target=character,
            source_item=item,
            magnitude=magnitude,
            duration=duration,
            expires_at=expires,
            is_active=True,
        )

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

