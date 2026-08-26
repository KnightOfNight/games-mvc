#!/usr/bin/env python3
"""MC door test agent (#279, V25.5) — operator-side throwaway, not repo code.

The mc_test_agent.py login/connect machinery with an interactive prompt
for the V25.5 agent-door vocabularies (protocol 2): type query/action
frames, see results and any tailed events as they arrive.

Usage:
    python3 mc_door_agent.py --url https://host[:port] \
        --username agent-smith --password '<password>' [--insecure]

Prompt commands (params are JSON objects):
    attach                             start the live tail on this connection
    ping                               ping/pong round trip
    query <kind> [{...}]               e.g.  query commands
                                             query where_is {"name": "Shy"}
    action <kind> {...}                e.g.  action answer {"to": "Shy", "text": "hi"}
                                             action strip {"name": "Shy"}
    raw {...}                          send any frame verbatim
    quit                               close and exit

Close codes: 4403 = not authorized, 4503 = killed (MC kill switch).
When the switch severs the connection, rerun the script to demonstrate
the connect-time refusal; after `mc restore`, rerun again to resume.

Dependencies: requests, websockets (already in venvs/mc-agent).
"""

import argparse
import asyncio
import atexit
import json
import os
import ssl
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
import websockets

try:  # line editing + history for input()
    import readline
    HISTORY_FILE = os.path.expanduser('~/.mc_door_agent_history')
    try:
        readline.read_history_file(HISTORY_FILE)
    except OSError:
        pass
    readline.set_history_length(500)
    atexit.register(readline.write_history_file, HISTORY_FILE)
except ImportError:  # readline is stdlib on macOS/Linux; degrade quietly
    readline = None


def exit_now(status=0):
    """Hard exit that survives a thread blocked in input(): save history
    first (atexit does not run under os._exit)."""
    if readline is not None:
        try:
            readline.write_history_file(HISTORY_FILE)
        except OSError:
            pass
    os._exit(status)

RESPONSE_TIMEOUT = 10  # seconds to wait for a result/pong before re-prompting

CLOSE_MEANINGS = {
    4403: 'not authorized (agents.shyland membership required)',
    4503: 'killed (the MC kill switch is engaged)',
}

QUERY_KINDS = ('commands', 'who_online', 'where_is', 'character', 'items',
               'is_admin', 'inventory', 'item')
ACTION_KINDS = ('answer', 'gift', 'create_artifact', 'strip', 'dress', 'move',
                'remove_item', 'edit_item', 'equip_item', 'unequip_item')


def log(line):
    stamp = datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3]
    print(f'[{stamp}Z] {line}', flush=True)


def django_login(base_url, username, password, verify):
    session = requests.Session()
    session.verify = verify
    login_url = f'{base_url}/accounts/login/'
    resp = session.get(login_url)
    resp.raise_for_status()
    csrf = session.cookies.get('csrftoken')
    if not csrf:
        sys.exit('login page set no csrftoken cookie — wrong URL?')
    resp = session.post(
        login_url,
        data={'username': username, 'password': password,
              'csrfmiddlewaretoken': csrf},
        headers={'Referer': login_url},
        allow_redirects=False,
    )
    if resp.status_code != 302 or not session.cookies.get('sessionid'):
        sys.exit(f'login failed for {username!r} (HTTP {resp.status_code})')
    return '; '.join(f'{c.name}={c.value}' for c in session.cookies)


def parse_command(line, next_id):
    """One prompt line -> a frame dict, or (None, error string)."""
    line = line.strip()
    if not line:
        return None, None
    verb, _, rest = line.partition(' ')
    rest = rest.strip()
    if verb == 'attach':
        return {'type': 'attach'}, None
    if verb == 'ping':
        return {'type': 'ping', 'nonce': next_id}, None
    if verb == 'raw':
        try:
            return json.loads(rest), None
        except ValueError as exc:
            return None, f'raw: bad JSON ({exc})'
    if verb in ('query', 'action'):
        kind, _, params_text = rest.partition(' ')
        if not kind:
            return None, f'{verb}: missing kind'
        params = {}
        if params_text.strip():
            try:
                params = json.loads(params_text)
            except ValueError as exc:
                return None, f'{verb} {kind}: params must be JSON ({exc})'
        frame = {'type': verb, 'id': f'op-{next_id}', 'params': params}
        frame['q' if verb == 'query' else 'act'] = kind
        return frame, None
    return None, (f'unknown command {verb!r} — try: attach, ping, '
                  f'query <kind>, action <kind>, raw, quit\n'
                  f'  query kinds:  {", ".join(QUERY_KINDS)}\n'
                  f'  action kinds: {", ".join(ACTION_KINDS)}')


def print_frame(frame):
    kind = frame.get('type')
    if kind == 'result':
        log('result <- ' + json.dumps(frame, ensure_ascii=False, indent=2))
    elif kind in ('pong', 'error'):
        log(json.dumps(frame, ensure_ascii=False))
    elif kind == 'hello':
        log(f'hello (protocol {frame.get("protocol")})')
    elif kind == 'gap':
        log(f'GAP: requested {frame.get("requested")}, '
            f'oldest surviving {frame.get("oldest")}')
    else:
        log(json.dumps(frame, ensure_ascii=False))


async def reader(ws, responses):
    """Route inbound frames: request responses (result/pong/error) onto
    the queue for the prompt loop to print in-line; tail events print as
    they arrive. Any server close exits the process immediately — the
    prompt thread cannot be interrupted, so a hard exit is the only way
    not to leave the operator at a dead prompt."""
    try:
        async for raw in ws:
            frame = json.loads(raw)
            if frame.get('type') in ('result', 'pong', 'error'):
                await responses.put(frame)
            else:
                print_frame(frame)
    except asyncio.CancelledError:  # normal quit path
        raise
    except websockets.exceptions.ConnectionClosed as exc:
        rcvd = getattr(exc, 'rcvd', None)
        code = getattr(exc, 'code', None) or (rcvd.code if rcvd else None)
        log(f'CLOSED: code {code} — '
            f'{CLOSE_MEANINGS.get(code, "server closed the connection")}')
        exit_now(0)
    log('server closed the connection.')
    exit_now(0)


async def repl(args):
    base = args.url.rstrip('/')
    parsed = urlparse(base)
    scheme = 'wss' if parsed.scheme == 'https' else 'ws'
    ws_url = f'{scheme}://{parsed.netloc}/ws/shyland/mc/'

    log(f'logging in as {args.username} at {base}')
    cookie = django_login(base, args.username, args.password,
                          verify=not args.insecure)
    ssl_ctx = None
    if scheme == 'wss':
        ssl_ctx = ssl.create_default_context()
        if args.insecure:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
    headers = {'Cookie': cookie, 'Origin': base}

    log(f'connecting to {ws_url}')
    try:
        connect = websockets.connect(ws_url, additional_headers=headers,
                                     ssl=ssl_ctx)
    except TypeError:
        connect = websockets.connect(ws_url, extra_headers=headers,
                                     ssl=ssl_ctx)

    next_id = 0
    try:
        async with connect as ws:
            responses = asyncio.Queue()
            reader_task = asyncio.create_task(reader(ws, responses))
            attached = False
            log('door open — type a command (help: any unknown word; quit to exit)')
            try:
                while True:
                    try:
                        line = await asyncio.to_thread(input, '> ')
                    except EOFError:
                        break
                    if line.strip() in ('quit', 'exit'):
                        break
                    if reader_task.done():
                        break
                    next_id += 1
                    frame, error = parse_command(line, next_id)
                    if error:
                        print(error)
                        continue
                    if frame is None:
                        continue
                    await ws.send(json.dumps(frame))
                    if frame.get('type') == 'attach' and not attached:
                        # A first attach's "response" is the tail itself.
                        attached = True
                        continue
                    # Every other frame draws exactly one discrete response
                    # (result, pong, or error) — print it before the next
                    # prompt so the prompt never goes stale.
                    try:
                        response = await asyncio.wait_for(
                            responses.get(), RESPONSE_TIMEOUT)
                    except asyncio.TimeoutError:
                        log(f'(no response within {RESPONSE_TIMEOUT}s)')
                        continue
                    if response is None:  # connection severed
                        break
                    print_frame(response)
            finally:
                reader_task.cancel()
    except websockets.exceptions.ConnectionClosed as exc:
        rcvd = getattr(exc, 'rcvd', None)
        code = getattr(exc, 'code', None) or (rcvd.code if rcvd else None)
        log(f'CLOSED: code {code} — '
            f'{CLOSE_MEANINGS.get(code, "server closed the connection")}')
        return
    log('detached.')


def main():
    parser = argparse.ArgumentParser(
        description='Interactive driver for the Shyland MC agent door.')
    parser.add_argument('--url', required=True,
                        help='base URL, e.g. https://host:40443')
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--insecure', action='store_true',
                        help='skip TLS verification (self-signed dev certs)')
    args = parser.parse_args()
    try:
        asyncio.run(repl(args))
    except KeyboardInterrupt:
        print()
        log('detached.')


if __name__ == '__main__':
    main()
