#!/usr/bin/env python3
"""MC test agent (#279) — operator-side throwaway, not part of the repo.

Connects to the Shyland MC egress and tails the event stream. When the
MC kill switch disconnects it (close 4503), it retries every minute —
logging each attempt — and resumes from the last event id it saw once
the switch is released.

Auth is the ordinary Django session: GET /accounts/login/ for the CSRF
token, POST the credentials, carry the session cookie into the WebSocket
handshake.

Usage:
    python3 mc_test_agent.py --url https://host:40443 \
        --username agent1 --password '<password>' [--after 1234-0] [--insecure]

Dependencies: requests, websockets  (pip install requests websockets)

Close codes worth knowing: 4403 = not authorized (not in agents.shyland),
4503 = killed (the MC kill switch is engaged).
"""

import argparse
import asyncio
import json
import ssl
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
import websockets

RETRY_SECONDS = 60

CLOSE_MEANINGS = {
    4403: 'not authorized (agents.shyland membership required)',
    4503: 'killed (the MC kill switch is engaged)',
}


def log(line):
    stamp = datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3]
    print(f'[{stamp}Z] {line}', flush=True)


def django_login(base_url, username, password, verify):
    """Return the session cookie header value after a normal form login."""
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


async def run_once(ws_url, headers, ssl_ctx, after, last_id):
    """One connect-attach-tail pass.

    Returns (close_code_or_None, last_seen_id). A None close code means
    the connection ended without a coded server close (normal EOF or a
    network drop).
    """
    try:
        connect = websockets.connect(ws_url, additional_headers=headers,
                                     ssl=ssl_ctx)
    except TypeError:  # older websockets releases use extra_headers
        connect = websockets.connect(ws_url, extra_headers=headers,
                                     ssl=ssl_ctx)

    try:
        async with connect as ws:
            attach = {'type': 'attach'}
            if after:
                attach['after'] = after
            async for raw in ws:
                frame = json.loads(raw)
                kind = frame.get('type')
                if kind == 'hello':
                    log(f'hello (protocol {frame.get("protocol")})')
                    await ws.send(json.dumps(attach))
                    log('attached — tailing the log (Ctrl-C to stop)'
                        + (f' from after {after}' if after else ''))
                elif kind == 'gap':
                    log(f'GAP: requested {frame.get("requested")}, '
                        f'oldest surviving {frame.get("oldest")}')
                else:
                    if frame.get('id'):
                        last_id = frame['id']
                    log(json.dumps(frame, ensure_ascii=False))
            return None, last_id
    except websockets.exceptions.ConnectionClosed as exc:
        rcvd = getattr(exc, 'rcvd', None)
        code = getattr(exc, 'code', None) or (rcvd.code if rcvd else None)
        meaning = CLOSE_MEANINGS.get(code, 'server closed the connection')
        log(f'CLOSED: code {code} — {meaning}')
        return code, last_id


async def tail(args):
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
    after = args.after
    last_id = None
    attempt = 0
    while True:
        if attempt == 0:
            log(f'connecting to {ws_url}')
        try:
            code, last_id = await run_once(ws_url, headers, ssl_ctx,
                                           after, last_id)
        except OSError as exc:
            sys.exit(f'connection failed: {exc}')
        if code != 4503:
            break
        # Kill-switch disconnect: keep trying every minute until the
        # switch is released, resuming from the last event id seen.
        attempt += 1
        after = last_id or after
        log(f'kill switch engaged — retrying every {RETRY_SECONDS}s'
            + (f' (will resume after {after})' if after else ''))
        await asyncio.sleep(RETRY_SECONDS)
        log(f'reconnect attempt {attempt}...')


def main():
    parser = argparse.ArgumentParser(
        description='Tail the Shyland MC event stream as a test agent.')
    parser.add_argument('--url', required=True,
                        help='base URL, e.g. https://host:40443')
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--after', default=None,
                        help='optional stream id to resume replay after')
    parser.add_argument('--insecure', action='store_true',
                        help='skip TLS verification (self-signed dev certs)')
    args = parser.parse_args()
    try:
        asyncio.run(tail(args))
    except KeyboardInterrupt:
        print()
        log('detached.')


if __name__ == '__main__':
    main()
