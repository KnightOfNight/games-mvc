#!/usr/bin/env python3
"""
Pre-start secrets guard.

Verifies that .env and TLS cert files exist before allowing
make start to proceed. Called by make check-secrets.

Exits 0 on success, 1 on any missing item.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"
SSL_DIR = REPO_ROOT / "ssl"

REQUIRED_ENV_KEYS = [
    "DOMAIN",
    "TLS_CERT_NAME",
    "SITE_TITLE",
    "DB_PASSWORD",
    "DJANGO_SECRET_KEY",
    "HOST_PORT",
    "DJANGO_SETTINGS_MODULE",
]


def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"')
    return env


def check() -> list[str]:
    errors = []

    if not ENV_FILE.exists():
        errors.append(".env not found — run 'make init' to generate it.")
        return errors

    env = load_env(ENV_FILE)

    for key in REQUIRED_ENV_KEYS:
        if not env.get(key):
            errors.append(f"Missing or empty: {key} in .env — run 'make init' to fix.")

    cert_name = env.get("TLS_CERT_NAME", "")
    if cert_name:
        for ext in (".crt", ".key"):
            p = SSL_DIR / f"{cert_name}{ext}"
            if not p.exists():
                errors.append(
                    f"Missing: ssl/{cert_name}{ext}\n"
                    f"  Place your TLS cert files in ssl/ or run 'make gen-certs'."
                )
    else:
        errors.append("TLS_CERT_NAME not set — cannot check cert files.")

    return errors


def main() -> int:
    errors = check()
    if not errors:
        print("check-secrets: all required files present")
        return 0

    print("check-secrets: FAILED\n", file=sys.stderr)
    for e in errors:
        for line in e.splitlines():
            print(f"  {line}", file=sys.stderr)
        print(file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
