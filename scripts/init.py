#!/usr/bin/env python3
"""
game-mvc first-time setup wizard.

Generates: .env

Run with: make init
          make setup   (wizard + build + start)

On re-run, existing values are read back and offered as defaults
so only changed fields need to be re-entered.
"""

import re
import secrets
import string
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_env(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def ask(prompt: str, default: str = "") -> str:
    display = f"{prompt} [{default}]: " if default else f"{prompt}: "
    value = input(display).strip()
    return value if value else default


def ask_required(prompt: str, default: str = "") -> str:
    while True:
        value = ask(prompt, default=default)
        if value:
            return value
        print("  (required — please enter a value)")


def section(title: str, subtitle: str = "") -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    print(f"{'─' * 60}")


def gen_secret(length: int = 50) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("game-mvc setup wizard")
    print("=" * 60)

    prev = load_env(ENV_FILE)
    rerun = bool(prev)

    if rerun:
        print("Existing config detected — press Enter to keep current values.")
    else:
        print("This wizard generates .env for your game-mvc deployment.")
        print("Your answers are saved locally and are gitignored.")
    print()

    # ------------------------------------------------------------------
    # Domain
    # ------------------------------------------------------------------
    section(
        "Domain name",
        "The hostname this server will be accessible at.",
    )
    print("  Example: battleship.private.magrathea.com")
    print()
    domain = ask_required("Domain name", default=prev.get("DOMAIN", ""))

    # ------------------------------------------------------------------
    # TLS certificate
    # ------------------------------------------------------------------
    section("TLS certificate")
    print("  Place your cert files in the ssl/ directory.")
    print("  The cert name is the filename prefix (without extension).")
    print()
    print("  Required files:")
    print("    ssl/<name>.crt  — full chain (domain cert + intermediates concatenated)")
    print("    ssl/<name>.key  — private key")
    print()
    print("  If your CA gives you separate files, combine them:")
    print("    cat domain.crt intermediate.crt > fullchain.crt")
    print()
    print("  For self-signed test certs (browser warning): make gen-certs")
    print()
    tls_cert_name = ask_required(
        "TLS cert name (filename prefix in ssl/)",
        default=prev.get("TLS_CERT_NAME", ""),
    )

    # ------------------------------------------------------------------
    # Site title
    # ------------------------------------------------------------------
    section("Site title", "Shown in the Django admin and auth pages.")
    site_title = ask("Site title", default=prev.get("SITE_TITLE", "game-mvc"))

    # ------------------------------------------------------------------
    # Database password
    # ------------------------------------------------------------------
    section("Database password")
    print("  Press Enter to auto-generate a strong random password.")
    print()
    db_password = ask(
        "DB password (Enter to generate)",
        default=prev.get("DB_PASSWORD", ""),
    )
    if not db_password:
        db_password = gen_secret(32)
        print(f"  Generated: {db_password}")

    # ------------------------------------------------------------------
    # Django secret key
    # ------------------------------------------------------------------
    section("Django secret key")
    print("  Press Enter to auto-generate.")
    print()
    secret_key = ask(
        "Django secret key (Enter to generate)",
        default=prev.get("DJANGO_SECRET_KEY", ""),
    )
    if not secret_key:
        secret_key = gen_secret(50)
        print(f"  Generated.")

    # ------------------------------------------------------------------
    # Host port
    # ------------------------------------------------------------------
    section("Host port", "SSL port this installation listens on.")
    print("  Default is 40443. Change if running multiple installations")
    print("  on the same machine (each needs a unique port).")
    print()
    host_port = ask("Host port", default=prev.get("HOST_PORT", "40443"))

    # ------------------------------------------------------------------
    # Write .env
    # ------------------------------------------------------------------
    section("Writing .env")

    env_lines = [
        "# Generated by make init — do not commit.",
        f"DOMAIN={domain}",
        f"TLS_CERT_NAME={tls_cert_name}",
        f"SITE_TITLE={site_title}",
        f"DB_PASSWORD={db_password}",
        f"DJANGO_SECRET_KEY={secret_key}",
        f"HOST_PORT={host_port}",
        f"DJANGO_SETTINGS_MODULE=game_mvc.settings.production",
        "",
    ]
    ENV_FILE.write_text("\n".join(env_lines))
    print(f"  wrote .env")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Setup complete.")
    print()
    print("Next steps:")
    print(f"  1. Place TLS cert files in ssl/:")
    print(f"       ssl/{tls_cert_name}.crt  (full chain)")
    print(f"       ssl/{tls_cert_name}.key  (private key)")
    print(f"     (or run: make gen-certs  for a self-signed test cert)")
    print()
    print(f"  2. Build and start:")
    print(f"       make build")
    print(f"       make start")
    print()
    print(f"  3. Run initial migrations:")
    print(f"       make migrate")
    print()
    print(f"  4. Create a superuser:")
    print(f"       docker compose exec django python manage.py createsuperuser")
    print()
    print(f"  Or do all of the above at once with: make setup")
    print()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nAborted.")
        sys.exit(1)
