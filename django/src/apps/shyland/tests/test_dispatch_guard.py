"""v20 brief 3 (#20): the dispatch guard.

A crashing command handler must produce one error-category line and a
server-side traceback log, and leave the connection alive. Exercised
directly against the dispatcher — no WebSocket handshake, no DB.
"""
import asyncio
from unittest import mock

from django.test import SimpleTestCase

from apps.shyland.consumers import SkylandConsumer


def make_consumer(sent):
    consumer = SkylandConsumer()
    consumer._character_is_dying = False

    async def fake_send_json(content, close=False):
        sent.append(content)

    consumer.send_json = fake_send_json
    return consumer


class DispatchGuardTests(SimpleTestCase):

    def test_crash_is_logged_reported_and_survivable(self):
        sent = []
        consumer = make_consumer(sent)

        async def run():
            boom = mock.AsyncMock(side_effect=RuntimeError('forced test crash'))
            with mock.patch.object(SkylandConsumer, 'cmd_look', boom):
                with self.assertLogs('shyland.commands', level='ERROR') as logs:
                    await consumer.receive_json({'text': 'look'})
            # The player got the echo (v20 brief 5, #15) then exactly
            # one error line…
            self.assertEqual(len(sent), 2)
            self.assertEqual(sent[0]['category'], 'echo')
            self.assertEqual(sent[0]['text'], '> look')
            self.assertEqual(sent[1]['category'], 'error')
            self.assertEqual(sent[1]['text'],
                             'Something went wrong with that command.')
            # …the full traceback landed server-side…
            joined = '\n'.join(logs.output)
            self.assertIn('RuntimeError', joined)
            self.assertIn('forced test crash', joined)
            self.assertIn('Traceback', joined)
            # …and the dispatcher still works afterwards.
            ok = mock.AsyncMock()
            with mock.patch.object(SkylandConsumer, 'cmd_who', ok):
                await consumer.receive_json({'text': 'who'})
            ok.assert_awaited_once()

        asyncio.run(run())

    def test_unknown_command_not_routed_through_guard_error(self):
        sent = []
        consumer = make_consumer(sent)
        asyncio.run(consumer.receive_json({'text': 'frobnicate'}))
        # Echo precedes the result even for unrecognized commands (#15).
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[0]['category'], 'echo')
        self.assertEqual(sent[0]['text'], '> frobnicate')
        self.assertEqual(sent[1]['category'], 'system')
        self.assertIn('Unknown command', sent[1]['text'])


class CompletionRequestTests(SimpleTestCase):
    """DB-free slices of the completion handler (#19)."""

    def test_non_grammar_verb_gets_empty_options(self):
        sent = []
        consumer = make_consumer(sent)
        asyncio.run(consumer.handle_complete('say hel'))
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['type'], 'complete')
        self.assertEqual(sent[0]['options'], [])

    def test_verb_position_gets_empty_options(self):
        # The client completes the verb position locally; the server
        # answers a bare-verb line with nothing.
        sent = []
        consumer = make_consumer(sent)
        asyncio.run(consumer.handle_complete('sell'))
        self.assertEqual(sent[0]['options'], [])
