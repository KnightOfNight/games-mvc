"""v22 Brief 6 (#135): the tick engine's effect-expiry async-safety fix.

The full-expiry branch of process_effects called the documented-sync
_expiry_message_for_effect bare in the async tick loop; its fresh ORM
query raised SynchronousOnlyOperation and killed the engine on every
full timed-effect expiry. These tests drive process_effects directly in
async context (the engine-harness style): before the fix, the full-
expiry case dies with SynchronousOnlyOperation; after it, the tick
completes, the message is delivered, the parent closes, and nothing is
left for the next sweep. The per-component sibling path is pinned
unchanged.
"""

from datetime import timedelta

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase
from django.utils import timezone

from apps.shyland.models import (
    Character, EffectComponent, EffectComponentInstance, EffectDefinition,
    EffectInstance,
)

from .test_command_revamp import make_character, make_world


def run_effects_engine():
    """Engine harness with stubbed delivery (CritProseTests style)."""
    from apps.shyland.management.commands.run_tick_engine import Command
    cmd = Command()
    player_msgs = []

    async def record_send(character_pk, text, category, status,
                          event=None, fight=None):
        if text:
            player_msgs.append((character_pk, text, category))

    async def record_broadcast(room_id, text, category='room',
                               exclude_pk=None, exclude_pks=None):
        pass
    cmd.send_to_player = record_send
    cmd.broadcast_to_room = record_broadcast
    return cmd, player_msgs


def make_timed_effect(prefix, char, components, expired_offsets):
    """One EffectInstance with stat_bonus components (no per-tick action);
    expired_offsets[i] < 0 puts component i's expiry in the past."""
    definition = EffectDefinition.objects.create(
        name=f'{prefix} Charm', slug=f'{prefix}-charm')
    instance = EffectInstance.objects.create(
        definition=definition, target=char, mk_tier=1, is_active=True)
    now = timezone.now()
    cis = []
    for i, (stat, magnitude) in enumerate(components):
        component = EffectComponent.objects.create(
            definition=definition, component_type='stat_bonus',
            target_stat=stat, order=i,
            magnitude_base=magnitude, magnitude_scaling=0.0,
            duration_base=60.0, duration_scaling=0.0,
        )
        cis.append(EffectComponentInstance.objects.create(
            effect_instance=instance, component=component,
            magnitude=magnitude, is_active=True,
            expires_at=now + timedelta(seconds=expired_offsets[i]),
        ))
    return definition, instance, cis


class FullExpiryTests(TransactionTestCase):

    async def test_full_expiry_completes_tick_delivers_and_closes(self):
        def setup():
            zone, room = make_world('teA')
            char = make_character('teA', room)
            # The buff is 'live': base 10 + 2 while active.
            Character.objects.filter(pk=char.pk).update(stat_str=12)
            return (char,) + make_timed_effect(
                'teA', char, [('str', 2)], [-5])
        char, definition, instance, cis = await sync_to_async(setup)()

        cmd, player_msgs = run_effects_engine()
        # Before the #135 fix this line raised SynchronousOnlyOperation.
        await cmd.process_effects(1)

        texts = [t for pk, t, c in player_msgs if pk == char.pk]
        self.assertIn('The teA Charm fades. Your body returns to normal.', texts)

        def state():
            inst = EffectInstance.objects.get(pk=instance.pk)
            ci = EffectComponentInstance.objects.get(pk=cis[0].pk)
            c = Character.objects.get(pk=char.pk)
            return (inst.is_active, inst.removed_by, ci.is_active, c.stat_str)
        is_active, removed_by, ci_active, stat_str = await sync_to_async(state)()
        self.assertFalse(is_active)
        self.assertEqual(removed_by, 'timeout')
        self.assertFalse(ci_active)
        self.assertEqual(stat_str, 10)   # the bonus reversed on expiry

        # No partial state: the next sweep finds nothing and says nothing.
        player_msgs.clear()
        await cmd.process_effects(2)
        self.assertEqual([t for pk, t, c in player_msgs if pk == char.pk], [])

    async def test_multi_component_full_expiry_single_message(self):
        def setup():
            zone, room = make_world('teB')
            char = make_character('teB', room)
            Character.objects.filter(pk=char.pk).update(stat_str=12, stat_dex=13)
            return (char,) + make_timed_effect(
                'teB', char, [('str', 2), ('dex', 3)], [-5, -5])
        char, definition, instance, cis = await sync_to_async(setup)()

        cmd, player_msgs = run_effects_engine()
        await cmd.process_effects(1)

        texts = [t for pk, t, c in player_msgs if pk == char.pk]
        # All components expiring together: ONE whole-effect message, no
        # per-component lines.
        self.assertEqual(
            texts.count('The teB Charm fades. Your body returns to normal.'), 1)
        self.assertFalse([t for t in texts if 'stat boost from' in t])

    async def test_per_component_sibling_path_unchanged(self):
        def setup():
            zone, room = make_world('teC')
            char = make_character('teC', room)
            Character.objects.filter(pk=char.pk).update(stat_str=12, stat_dex=13)
            return (char,) + make_timed_effect(
                'teC', char, [('str', 2), ('dex', 3)], [-5, 3600])
        char, definition, instance, cis = await sync_to_async(setup)()

        cmd, player_msgs = run_effects_engine()
        await cmd.process_effects(1)

        texts = [t for pk, t, c in player_msgs if pk == char.pk]
        self.assertIn('The stat boost from teC Charm fades.', texts)

        def state():
            inst = EffectInstance.objects.get(pk=instance.pk)
            expired = EffectComponentInstance.objects.get(pk=cis[0].pk)
            live = EffectComponentInstance.objects.get(pk=cis[1].pk)
            return (inst.is_active, expired.is_active, live.is_active)
        inst_active, expired_active, live_active = await sync_to_async(state)()
        self.assertTrue(inst_active)     # the parent survives
        self.assertFalse(expired_active)
        self.assertTrue(live_active)
