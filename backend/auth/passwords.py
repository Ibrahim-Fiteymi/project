"""Password hashing.

Bcrypt via passlib. The `truncate_error=False` flag silences passlib's bcrypt
length warning while preserving the standard 72-byte ceiling — passwords longer
than 72 bytes are silently truncated by bcrypt itself, which is industry
standard behaviour and what every other bcrypt-backed system does.
"""

from __future__ import annotations

from passlib.context import CryptContext

_pwd = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return _pwd.verify(plain, hashed)
    except ValueError:
        # Malformed hash in the DB (e.g. legacy "!disabled" sentinel).
        return False


def needs_rehash(hashed: str) -> bool:
    return _pwd.needs_update(hashed)
