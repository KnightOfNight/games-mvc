"""v24.30 Brief 1 — uniform config setters (#251).

The four settings commands share one helper, but their setters did not
share one shape: three wrote only the DB row and left the cached
``self.character`` attribute to the calling ``cmd_*``, so the cache was
right only by the caller's cooperation and any direct setter call left it
stale. The ruling (operator, 2026-08-15, #251) makes every setter the
single writer of both — ``_set_plunder_mode``'s v24.29 shape, generalized
— and the caller-side assignments are gone with it.

Zero player-visible behavior change, so this suite pins two things: the
setter-owns-both invariant (§5.1–2) and the absence of drift in what the
commands actually say (§5.3).
"""

from asgiref.sync import sync_to_async
from django.test import TransactionTestCase

from apps.shyland.models import Character

from .test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)


def texts_and_categories(sent):
    return [(m['text'], m['category']) for m in outputs(sent)]


# The family, one row per setting: the setter's name, the model field it
# owns, and the command that drives it.
SETTINGS = [
    ('_set_brief_mode', 'brief_mode', 'cmd_brief'),
    ('_set_show_timestamps', 'show_timestamps', 'cmd_timestamps'),
    ('_set_echo_mode', 'echo_mode', 'cmd_echo'),
    ('_set_plunder_mode', 'plunder_mode', 'cmd_plunder'),
]


class SetterOwnsBothTests(TransactionTestCase):
    """§5.1: the issue's exact complaint — "any direct call to a setter
    leaves ``self.character`` stale" — as a pinned regression. Calling the
    setter directly is the point: it bypasses every caller, so only the
    setter itself can keep the cache honest."""

    async def test_each_setter_writes_row_and_cache(self):
        zone, room = await sync_to_async(make_world)('sob')

        for i, (setter_name, field, _cmd) in enumerate(SETTINGS):
            char = await sync_to_async(make_character)(f'sob{i}', room)
            consumer = make_stub_consumer(char, [])
            setter = getattr(consumer, setter_name)

            # Both directions, so the assertion never rides the default.
            for value in (True, False):
                await setter(value)
                fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
                msg = f'{setter_name}({value})'
                self.assertEqual(getattr(fresh, field), value, msg=msg)
                self.assertEqual(getattr(consumer.character, field), value,
                                 msg=msg)


class CommandCacheCoherenceTests(TransactionTestCase):
    """§5.2: with the caller-side assignments removed, the row and the
    cache must still agree after every command. ``timestamps`` pins the
    third instance of the old fragility (§2 claim 3): its set path bypasses
    ``_cmd_setting`` and called the setter directly, correct only because
    a later fresh fetch happened to replace ``self.character`` wholesale."""

    async def test_each_command_leaves_row_and_cache_in_step(self):
        zone, room = await sync_to_async(make_world)('ccc')

        for i, (_setter, field, cmd_name) in enumerate(SETTINGS):
            char = await sync_to_async(make_character)(f'ccc{i}', room)
            sent = []
            consumer = make_stub_consumer(char, sent)
            command = getattr(consumer, cmd_name)

            for word, expected in [('on', True), ('off', False)]:
                sent.clear()
                await command(word)
                fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
                msg = f'{cmd_name} {word}'
                self.assertEqual(getattr(fresh, field), expected, msg=msg)
                self.assertEqual(getattr(consumer.character, field), expected,
                                 msg=msg)


class NoBehaviorDriftTests(TransactionTestCase):
    """§5.3: the release removes lines, not behavior. The sentences are the
    v22 settings standard, unchanged; ``cmd_brief`` and ``cmd_plunder``
    lost their ``if value is not None`` blocks entirely, so their bare and
    invalid paths are worth re-pinning here."""

    # The bare-report sentence each command answers with at its default.
    BARE = [
        ('cmd_brief', 'brief room display is off.'),
        ('cmd_echo', 'command echo is on.'),
        ('cmd_plunder', 'plunder is off.'),
        ('cmd_timestamps', 'output timestamps are on.'),
    ]

    async def test_bare_still_reports_the_current_setting(self):
        zone, room = await sync_to_async(make_world)('drift1')

        for i, (cmd_name, sentence) in enumerate(self.BARE):
            char = await sync_to_async(make_character)(f'd1{i}', room)
            sent = []
            consumer = make_stub_consumer(char, sent)
            await getattr(consumer, cmd_name)('')
            self.assertEqual(texts_and_categories(sent),
                             [(sentence, 'system')], msg=cmd_name)

    async def test_invalid_input_answers_usage_and_changes_nothing(self):
        zone, room = await sync_to_async(make_world)('drift2')

        for i, (_setter, field, cmd_name) in enumerate(SETTINGS):
            char = await sync_to_async(make_character)(f'd2{i}', room)
            before = getattr(char, field)
            sent = []
            consumer = make_stub_consumer(char, sent)

            await getattr(consumer, cmd_name)('banana')
            usage = f'Usage: {cmd_name[len("cmd_"):]} [on|off]'
            self.assertEqual(texts_and_categories(sent),
                             [(usage, 'error')], msg=cmd_name)
            fresh = await sync_to_async(Character.objects.get)(pk=char.pk)
            self.assertEqual(getattr(fresh, field), before, msg=cmd_name)
            self.assertEqual(getattr(consumer.character, field), before,
                             msg=cmd_name)
