"""v24.27 brief 1 (#234): character hard delete.

Hard delete is the ruling: the admin console is the only deletion
surface, and the entire inventory dies with the character —
`ItemInstance.owner` is CASCADE (0046). Pre-existing SET_NULL orphans
(owner, current_room, and corpse all NULL — outside the
exactly-one-location invariant, unreachable by any game path) are swept
by the 0047 data migration. World items (room drops) and corpse
contents survive; corpses the character killed survive with
`killed_by=NULL`; the auth User survives; the name frees for reuse.
A deleted-while-connected consumer routes to the character creator, and
a combat session emptied of characters closes through the standard
close path with its NPCs released.
"""
import asyncio
import contextlib
import io
from datetime import timedelta
from importlib import import_module

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.apps import apps as live_apps
from django.contrib.auth.models import User
from django.db.models import CASCADE
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    Character, CombatSession, COMBAT_ROUND_TICKS, Corpse,
    ItemDefinition, ItemInstance, NpcInstance,
)

from .test_combat_state import (
    make_character, make_npc, make_npc_definition, make_world,
)
from .test_zombie_sessions import make_engine, make_session

NO_CHARACTER_LINE = 'No character found. Create one to play.'


def make_item_definition(prefix):
    return ItemDefinition.objects.create(
        name=f'{prefix} Trinket', slug=f'{prefix}-trinket',
        item_type=ItemDefinition.ACCESSORY, genre_tag=ItemDefinition.FANTASY,
        description='A test item.',
        scaling_base=1.0, scaling_factor=0.0,
        # v25.12 (#311): explicit all-worn band — preserves the
        # retired empty-table fallback these fixtures ran under.
        durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
    )


def make_item(definition, **kwargs):
    return ItemInstance.objects.create(
        definition=definition, mk_tier=1, rarity=ItemInstance.COMMON,
        **kwargs,
    )


def make_corpse(room, killed_by=None):
    return Corpse.objects.create(
        npc_name_snapshot='cave spider', current_room=room,
        killed_by=killed_by, decay_at=timezone.now() + timedelta(hours=1),
    )


class HardDeleteCascadeTests(TestCase):
    """The owner CASCADE (0046): inventory dies, world items survive."""

    def setUp(self):
        self.zone, self.room = make_world('hd')
        self.char = make_character('hd', self.room)
        self.definition = make_item_definition('hd')

    def test_owner_on_delete_is_cascade(self):
        self.assertIs(
            ItemInstance._meta.get_field('owner').remote_field.on_delete,
            CASCADE,
        )

    def test_delete_cascades_inventory_and_spares_world_items(self):
        held = make_item(self.definition, owner=self.char)
        equipped = make_item(
            self.definition, owner=self.char,
            is_equipped=True, equipped_slot='NECK',
        )
        bound = make_item(
            self.definition, owner=self.char,
            is_equipped=True, equipped_slot='RING',
            is_soulbound=True, soulbound_to=self.char,
        )
        room_item = make_item(self.definition, current_room=self.room)
        corpse = make_corpse(self.room)
        corpse_item = make_item(self.definition, corpse=corpse)

        self.char.delete()

        for pk in (held.pk, equipped.pk, bound.pk):
            self.assertFalse(ItemInstance.objects.filter(pk=pk).exists())
        room_item.refresh_from_db()
        self.assertIsNone(room_item.owner_id)
        self.assertEqual(room_item.current_room_id, self.room.pk)
        corpse_item.refresh_from_db()
        self.assertIsNone(corpse_item.owner_id)
        self.assertEqual(corpse_item.corpse_id, corpse.pk)

    def test_delete_leaves_no_orphan_shape(self):
        make_item(self.definition, owner=self.char)
        make_item(
            self.definition, owner=self.char,
            is_equipped=True, equipped_slot='NECK',
        )
        make_item(self.definition, current_room=self.room)

        self.char.delete()

        self.assertEqual(
            ItemInstance.objects.filter(
                owner__isnull=True,
                current_room__isnull=True,
                corpse__isnull=True,
            ).count(),
            0,
        )

    def test_survivors_corpse_user_and_loot_rights(self):
        corpse = make_corpse(self.room, killed_by=self.char)
        user_pk = self.char.user_id
        char_pk = self.char.pk

        self.char.delete()

        corpse.refresh_from_db()
        self.assertIsNone(corpse.killed_by_id)
        self.assertEqual(corpse.npc_name_snapshot, 'cave spider')
        self.assertTrue(User.objects.filter(pk=user_pk).exists())
        # Loot rights are gone: the killed_by predicate can never match.
        self.assertFalse(Corpse.objects.filter(killed_by_id=char_pk).exists())

    def test_name_frees_for_case_insensitive_reuse(self):
        origin = self.char.origin
        archetype = self.char.archetype
        name = self.char.name

        self.char.delete()

        user2 = User.objects.create_user(username='hd_user2', password='x')
        again = Character.objects.create(
            user=user2, name=name.lower(),
            origin=origin, archetype=archetype,
            current_room=self.room,
        )
        self.assertIsNotNone(again.pk)
        self.assertEqual(again.name, name.lower())


class OrphanCleanupMigrationTests(TestCase):
    """The 0047 predicate: all-NULL-location rows die, nothing else."""

    def setUp(self):
        self.zone, self.room = make_world('oc')
        self.char = make_character('oc', self.room)
        self.definition = make_item_definition('oc')

    def test_predicate_removes_orphan_and_touches_nothing_else(self):
        orphan = make_item(self.definition, owner=self.char)
        keeper = make_item(self.definition, owner=self.char)
        room_item = make_item(self.definition, current_room=self.room)
        corpse_item = make_item(self.definition, corpse=make_corpse(self.room))
        # Forge the orphan the way real orphans were made: a bulk update
        # around save(), exactly like the deletion collector's SET_NULL.
        ItemInstance.objects.filter(pk=orphan.pk).update(owner=None)

        migration = import_module(
            'apps.shyland.migrations.0047_delete_orphaned_item_instances')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            migration.delete_orphans(live_apps, None)

        self.assertFalse(ItemInstance.objects.filter(pk=orphan.pk).exists())
        for pk in (keeper.pk, room_item.pk, corpse_item.pk):
            self.assertTrue(ItemInstance.objects.filter(pk=pk).exists())
        self.assertIn('deleted 1 orphaned ItemInstance row(s)', buf.getvalue())


class ZeroCharacterSessionCloseTests(TransactionTestCase):
    """Deleting an in-combat character empties the session's character
    side (M2M through-rows cascade); the combat pass closes it through
    the standard close path with its NPCs released and restored."""

    def test_character_empty_session_closes_with_npcs_released(self):
        zone, room = make_world('zc')
        char = make_character('zc', room)
        definition = make_npc_definition('zc')
        npc = make_npc(definition, room, hp=20)
        # Damage the NPC so the release's full restore is observable.
        NpcInstance.objects.filter(pk=npc.pk).update(vitality_current=5)
        # tick_counter lands on a round boundary on the next tick — the
        # participants load is the trigger (per-tick query discipline).
        session = make_session(
            char, [npc], room, tick_counter=COMBAT_ROUND_TICKS - 1)

        char.delete()
        self.assertEqual(session.characters.count(), 0)

        cmd = make_engine()
        asyncio.run(cmd.process_combat(1))

        session.refresh_from_db()
        self.assertFalse(session.is_active)
        npc.refresh_from_db()
        self.assertTrue(npc.is_alive)
        self.assertEqual(npc.vitality_current, npc.vitality_max)
        # release_session_npcs clears membership last.
        self.assertEqual(session.npcs.count(), 0)


class DeletedWhileConnectedTests(TransactionTestCase):
    """The consumer guard: a command after a mid-session hard delete gets
    the connect-time no-character routing — error line, redirect envelope
    to the creator, closed socket — never an unhandled crash."""

    async def _drain_until_map(self, communicator):
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            if msg.get('type') == 'map':
                return

    async def test_command_after_delete_routes_to_creator(self):
        zone, room = await sync_to_async(make_world)('Deleted')
        character = await sync_to_async(make_character)('Deleted', room)

        communicator = WebsocketCommunicator(
            SkylandConsumer.as_asgi(), '/ws/shyland/',
        )
        communicator.scope['user'] = character.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await self._drain_until_map(communicator)

        await sync_to_async(
            lambda: Character.objects.get(pk=character.pk).delete())()
        await communicator.send_json_to({'text': 'wallet'})

        msgs = []
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            msgs.append(msg)
            if msg.get('type') == 'redirect':
                break

        error = next(
            m for m in msgs
            if m.get('type') == 'output' and m.get('text') == NO_CHARACTER_LINE)
        self.assertEqual(error.get('category'), 'error')
        redirect = msgs[-1]
        self.assertEqual(redirect['url'], '/shyland/create/')

        close = await communicator.receive_output(timeout=10)
        self.assertEqual(close['type'], 'websocket.close')
        await communicator.disconnect()
