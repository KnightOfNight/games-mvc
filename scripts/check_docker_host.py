#!/usr/bin/env python3
"""
Session pre-flight deployment-target check (see CLAUDE.md).

Standing rule: DOCKER_HOST set — any value — means PRODUCTION; unset
means the local dev daemon. This check identifies the target, verifies
.env matches the target's env file (.env.prod / .env.dev), and verifies
the daemon is reachable. It is check-only: it never copies, repairs, or
falls back to a different daemon.

Exit codes:
  0 — target identified, posture coherent, daemon reachable; proceed.
  1 — daemon unreachable; hard blocker, stop and report.
  2 — posture incoherent (.env missing, or not matching the target's
      env file); stop and report. Never repair .env to pass a check.
"""

import filecmp
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def daemon_reachable():
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return False, "docker CLI not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "docker info timed out"
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, result.stdout.strip()


def main() -> int:
    docker_host = os.environ.get("DOCKER_HOST", "").strip()
    target = "PRODUCTION" if docker_host else "local dev"
    env_file = ".env.prod" if docker_host else ".env.dev"

    if docker_host:
        print(f"DOCKER_HOST={docker_host} — target is PRODUCTION.")
    else:
        print("DOCKER_HOST is not set — target is the local dev daemon.")

    env = REPO_ROOT / ".env"
    ref = REPO_ROOT / env_file
    if not ref.is_file():
        print(f"BLOCKER: {env_file} is missing — posture cannot be verified.")
        print("Stop and report to the operator.")
        return 2
    if not env.is_file():
        print(f"BLOCKER: .env is missing — posture must be set deliberately (cp {env_file} .env).")
        print("Stop and report to the operator.")
        return 2
    if not filecmp.cmp(env, ref, shallow=False):
        print(f"BLOCKER: posture mismatch — .env does not match {env_file}.")
        print("Stop and report to the operator. Never repair .env to satisfy a check.")
        return 2
    print(f"Posture OK: .env matches {env_file}.")

    ok, detail = daemon_reachable()
    if not ok:
        print(f"BLOCKER: {target} daemon unreachable — {detail}")
        if docker_host:
            print("Stop the brief and report (a missing SSH key is a common cause).")
        else:
            print("Stop and report (is the local Docker daemon running?).")
        return 1
    print(f"Daemon reachable: {detail}")
    print(f"Pre-flight OK — session target: {target}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
