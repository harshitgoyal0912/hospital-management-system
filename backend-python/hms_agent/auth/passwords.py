"""Password hashing.

The existing code passes ``password_hash`` in as a *parameter* to create_user
(multi_agent_server.py:562), which means hashing happens somewhere outside the
server's control — or not at all. Hashing belongs here, on the server, behind a
function that callers cannot bypass.
"""
from __future__ import annotations

import bcrypt

#: Work factor. Raise over time; `needs_rehash` detects credentials below it.
ROUNDS = 12


def hash_password(plaintext: str) -> str:
    if not plaintext:
        raise ValueError("refusing to hash an empty password")
    salt = bcrypt.gensalt(rounds=ROUNDS)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, stored_hash: str) -> bool:
    """Constant-time verification that never raises on malformed input.

    A malformed or legacy hash returns False rather than propagating, so a bad
    row in the users table cannot become a 500 that distinguishes it from a
    wrong password.
    """
    if not plaintext or not stored_hash:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """True if the stored hash predates the current work factor or is not bcrypt.

    The seeded demo rows use literal strings like ``hashed_password_101``
    (setup_database.py:53); those are not bcrypt hashes and must be treated as
    unusable credentials rather than valid ones.
    """
    if not stored_hash or not stored_hash.startswith("$2"):
        return True
    try:
        cost = int(stored_hash.split("$")[2])
    except (IndexError, ValueError):
        return True
    return cost < ROUNDS
