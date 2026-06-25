from __future__ import annotations

import hmac
import secrets


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def extract_bearer_token(header: str | None) -> str | None:
    if not header:
        return None
    prefix = "Bearer "
    if not header.startswith(prefix):
        return None
    token = header[len(prefix) :].strip()
    return token or None


def token_matches(expected: str, supplied: str | None) -> bool:
    if not expected or not supplied:
        return False
    return hmac.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8"))


def is_valid_bridge_bind(host: str) -> bool:
    return host == "127.0.0.1"
