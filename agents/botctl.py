#!/usr/bin/env python3
"""botctl — the bot manager (#295, V25.7).

One command to start, stop, restart, status, or tail a Shyland agent
bot against a named target. Stdlib-only and compatible with the system
python3 (3.9): the manager itself needs no venv — it is the tool that
reports a missing one.

Self-locating: the repo root is the parent of this file's directory,
so THE COPY YOU RUN IS THE CHECKOUT IT MANAGES — the main checkout for
prod, the current version worktree for dev. No baked-in absolute paths.

Usage:
    botctl.py <prod|dev> <start|stop|restart|status|tail> [--bot NAME]

Per (--bot NAME, target) — default bot sudo — the manager derives
(v25.8, #299: state is (bot, target)-scoped, so one checkout can host a
dev-facing and a prod-facing bot side by side and a dev stop can never
touch the prod bot):
    module    agents/<name>_bot.py
    log       agents/<name>_bot.<target>.log
    key file  agents/.secrets/anthropic-api-key.<name>
    pid file  agents/.<name>_bot.<target>.pid        (bot-owned)
    convos    agents/.<name>_bot_conversations.<target>.json (bot-owned)

The key is read at start and placed in the child environment only —
never argv, never echoed, never logged. This file contains no secret
values.
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENTS_DIR.parent
VENV_PYTHON = AGENTS_DIR / 'venvs' / 'mc-agent' / 'bin' / 'python'

# ----------------------------------------------------------------------
# Targets — the two stacks a bot can face. dev runs self-signed certs,
# so it (and only it) rides --insecure; the prod path can never receive
# it. URLs are rstripped again at use (belt and suspenders with #292).
# ----------------------------------------------------------------------
TARGETS = {
    'prod': {'url': 'https://games.magrathea.com', 'insecure': False},
    'dev': {'url': 'https://emma.private.magrathea.com', 'insecure': True},
}

STATUS_POLL_TRIES = 20
STATUS_POLL_DELAY = 0.5  # ~10 s bounded, no blind sleeps
TAIL_LINES = 10


def stamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')


def say(line):
    print(f'[{stamp()}] {line}', flush=True)


class BotPaths:
    def __init__(self, name, target):
        self.name = name
        self.target = target
        self.module = AGENTS_DIR / f'{name}_bot.py'
        self.log = AGENTS_DIR / f'{name}_bot.{target}.log'
        self.key_file = AGENTS_DIR / '.secrets' / f'anthropic-api-key.{name}'
        # Bot-owned (the bot derives them from its own --target); listed
        # here so humans debugging state files have the one map (#299).
        self.pid_file = AGENTS_DIR / f'.{name}_bot.{target}.pid'
        self.convo_file = (AGENTS_DIR
                           / f'.{name}_bot_conversations.{target}.json')


def fail(message):
    print(f'botctl: {message}', file=sys.stderr)
    return 1


def check_prereqs(paths, need_key):
    """Clear errors, never repairs: the missing venv names its fix and
    is never auto-installed."""
    if not paths.module.is_file():
        return fail(f'no bot module at {paths.module}')
    if not VENV_PYTHON.is_file():
        return fail(
            f'no venv python at {VENV_PYTHON} — create it with:\n'
            f'  python3 -m venv {AGENTS_DIR / "venvs" / "mc-agent"} && '
            f'{VENV_PYTHON} -m pip install -r '
            f'{AGENTS_DIR / "requirements.txt"}')
    if need_key and not paths.key_file.is_file():
        return fail(f'no key file at {paths.key_file}')
    return 0


def bot_command(paths, *sub, **popen_kwargs):
    """Run one bot subcommand through the venv python, list-argv."""
    argv = [str(VENV_PYTHON), str(paths.module)] + list(sub)
    return subprocess.run(argv, cwd=str(REPO_ROOT), **popen_kwargs)


def bot_status(paths, quiet=False):
    kwargs = {}
    if quiet:
        kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
    return bot_command(paths, 'status', '--target', paths.target,
                       **kwargs).returncode


def poll_status(paths, want_running):
    """Bounded wait for the bot's own status to report the desired
    state. True when reached."""
    for _ in range(STATUS_POLL_TRIES):
        running = bot_status(paths, quiet=True) == 0
        if running == want_running:
            return True
        time.sleep(STATUS_POLL_DELAY)
    return False


def short_tail(paths):
    if paths.log.is_file():
        say(f'last {TAIL_LINES} log lines ({paths.log}):')
        subprocess.run(['tail', '-n', str(TAIL_LINES), str(paths.log)])
    else:
        say(f'no log file yet at {paths.log}')


def cmd_start(target, paths):
    rc = check_prereqs(paths, need_key=True)
    if rc:
        return rc
    if bot_status(paths, quiet=True) == 0:
        say(f'{paths.name} bot already running — nothing to do')
        return 0
    key = paths.key_file.read_text().strip()
    if not key:
        return fail(f'key file {paths.key_file} is empty')
    # Child environment only: never argv, never echoed, never logged.
    env = dict(os.environ)
    env['ANTHROPIC_API_KEY'] = key
    url = TARGETS[target]['url'].rstrip('/')
    argv = [str(VENV_PYTHON), str(paths.module), 'run',
            '--target', target, '--url', url, '--log', str(paths.log)]
    if TARGETS[target]['insecure']:
        argv.append('--insecure')
    say(f'starting {paths.name} bot against {target} ({url})')
    with open(paths.log, 'ab') as log_fh:
        subprocess.Popen(
            argv, cwd=str(REPO_ROOT), env=env, start_new_session=True,
            stdin=subprocess.DEVNULL, stdout=log_fh,
            stderr=subprocess.STDOUT)
    if not poll_status(paths, want_running=True):
        say(f'{paths.name} bot did not reach running within '
            f'{int(STATUS_POLL_TRIES * STATUS_POLL_DELAY)}s')
        short_tail(paths)
        return 1
    say(f'{paths.name} bot running')
    short_tail(paths)
    return 0


def cmd_stop(target, paths):
    rc = check_prereqs(paths, need_key=False)
    if rc:
        return rc
    if bot_status(paths, quiet=True) != 0:
        say(f'{paths.name} bot ({target}) not running — nothing to stop')
        return 1
    result = bot_command(paths, 'stop', '--target', target)
    if result.returncode != 0:
        return result.returncode
    if not poll_status(paths, want_running=False):
        say(f'{paths.name} bot ({target}) still up after '
            f'{int(STATUS_POLL_TRIES * STATUS_POLL_DELAY)}s')
        short_tail(paths)
        return 1
    say(f'{paths.name} bot ({target}) stopped')
    short_tail(paths)
    return 0


def cmd_restart(target, paths):
    rc = check_prereqs(paths, need_key=True)
    if rc:
        return rc
    if bot_status(paths, quiet=True) == 0:
        rc = cmd_stop(target, paths)
        if rc:
            return rc
    else:
        say(f'{paths.name} bot ({target}) not running — going straight '
            f'to start')
    return cmd_start(target, paths)


def cmd_status(target, paths):
    rc = check_prereqs(paths, need_key=False)
    if rc:
        return rc
    # Pass-through: the bot's own status line and exit code are the
    # answer (target-scoped since #299).
    return bot_status(paths)


def cmd_tail(paths):
    if not paths.log.is_file():
        return fail(f'no log file at {paths.log}')
    say(f'following {paths.log} (Ctrl-C to stop)')
    try:
        subprocess.run(['tail', '-f', str(paths.log)])
    except KeyboardInterrupt:
        pass
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Manage a Shyland agent bot (#295).')
    parser.add_argument('target', choices=sorted(TARGETS),
                        help='which stack the bot faces')
    parser.add_argument('command',
                        choices=['start', 'stop', 'restart', 'status',
                                 'tail'])
    parser.add_argument('--bot', default='sudo',
                        help='bot name (default: sudo)')
    args = parser.parse_args()
    paths = BotPaths(args.bot, args.target)
    if args.command == 'start':
        return cmd_start(args.target, paths)
    if args.command == 'stop':
        return cmd_stop(args.target, paths)
    if args.command == 'restart':
        return cmd_restart(args.target, paths)
    if args.command == 'status':
        return cmd_status(args.target, paths)
    return cmd_tail(paths)


if __name__ == '__main__':
    sys.exit(main())
