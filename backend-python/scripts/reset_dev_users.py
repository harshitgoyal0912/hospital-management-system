"""Give the seeded development users real, usable credentials.

`setup_database.py:53` writes literal strings like ``hashed_password_101`` into
`users.password_hash`. Those are not bcrypt hashes, so `needs_rehash` treats them
as unusable and nobody can log in — which is correct, but it leaves the
development database with no working accounts.

This mints a random password per user, stores a bcrypt hash, and prints the
plaintext once. Passwords are never written to the repository or to a file.

    python scripts/reset_dev_users.py --list
    python scripts/reset_dev_users.py --apply

Refuses to run against anything that does not look like a local database unless
--i-know-this-is-not-local is passed, so it cannot be pointed at production by
accident.
"""
from __future__ import annotations

import argparse
import os
import secrets
import string
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure") and sys.stderr:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hms_agent.auth.passwords import hash_password  # noqa: E402

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db", "postgres", ""}
ALPHABET = string.ascii_letters + string.digits


def generate_password(length: int = 20) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def is_local(database_url: str) -> bool:
    try:
        return (urlparse(database_url).hostname or "") in LOCAL_HOSTS
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the new hashes")
    parser.add_argument("--list", action="store_true", help="show users without changing anything")
    parser.add_argument("--i-know-this-is-not-local", action="store_true",
                        help="permit a non-local DATABASE_URL")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        return 2

    if not is_local(database_url) and not args.i_know_this_is_not_local:
        host = urlparse(database_url).hostname
        print(f"refusing to run against non-local host {host!r}.", file=sys.stderr)
        print("re-run with --i-know-this-is-not-local if that is genuinely intended.",
              file=sys.stderr)
        return 2

    from database import SessionLocal, User  # noqa: E402

    session = SessionLocal()
    try:
        users = session.query(User).all()
        if not users:
            print("no users found.")
            return 0

        if args.list or not args.apply:
            print(f"{'username':24} {'role':14} usable credential?")
            print("-" * 60)
            for u in users:
                ok = bool(u.password_hash) and u.password_hash.startswith("$2")
                print(f"{u.username or '':24} {u.role or '':14} {'yes' if ok else 'NO'}")
            if not args.apply:
                print("\nnothing changed. re-run with --apply to reset passwords.")
            return 0

        print(f"{'username':24} {'role':14} password")
        print("-" * 64)
        for u in users:
            password = generate_password()
            u.password_hash = hash_password(password)
            print(f"{u.username or '':24} {u.role or '':14} {password}")
        session.commit()
        print("\nStored as bcrypt hashes. These passwords are shown once and not saved.")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
