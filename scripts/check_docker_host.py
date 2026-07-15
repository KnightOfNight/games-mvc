#!/usr/bin/env python3
"""
Session pre-flight deployment-target check (see CLAUDE.md).

Verifies that DOCKER_HOST is set and that the Docker daemon it points
at is reachable. Never falls back to a local daemon.

Exit codes:
  0 — DOCKER_HOST set and reachable; safe to proceed.
  1 — DOCKER_HOST set but unreachable; hard blocker, stop the brief.
  2 — DOCKER_HOST not set; ask the operator before touching anything.
"""

import os
import subprocess
import sys


def main() -> int:
    docker_host = os.environ.get("DOCKER_HOST", "").strip()

    if not docker_host:
        print("DOCKER_HOST is not set.")
        print("Do NOT assume a local Docker daemon is the intended target.")
        print("Ask the operator whether to proceed locally or stop the brief.")
        return 2

    print(f"DOCKER_HOST={docker_host}")

    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        print("BLOCKER: docker CLI not found on PATH.")
        return 1
    except subprocess.TimeoutExpired:
        print("BLOCKER: docker info timed out — target unreachable.")
        print("Stop the brief and report to the operator (a missing SSH key is a common cause).")
        return 1

    if result.returncode != 0:
        print("BLOCKER: docker info failed — target unreachable.")
        print(result.stderr.strip())
        print("Stop the brief and report to the operator (a missing SSH key is a common cause).")
        return 1

    print(f"Target reachable: {result.stdout.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
