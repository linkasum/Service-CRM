"""
Signed Telegram link tokens for bot account binding.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time

from core.config import get_settings

TELEGRAM_LINK_TOKEN_TTL_SECONDS = 15 * 60
_TOKEN_PREFIX = "t"
_TOKEN_VERSION = 1
_SIGNATURE_BYTES = 16


def _secret() -> bytes:
    settings = get_settings()
    return f"{settings.SECRET_KEY}:{settings.TELEGRAM_BOT_TOKEN}".encode("utf-8")


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_telegram_link_token(
    user_id: int,
    ttl_seconds: int = TELEGRAM_LINK_TOKEN_TTL_SECONDS,
) -> tuple[str, int]:
    expires_at = int(time.time()) + ttl_seconds
    nonce = secrets.randbits(32)
    payload = struct.pack(">BIII", _TOKEN_VERSION, int(user_id), expires_at, nonce)
    signature = hmac.new(_secret(), payload, hashlib.sha256).digest()[:_SIGNATURE_BYTES]
    return _TOKEN_PREFIX + _b64_encode(payload + signature), expires_at


def verify_telegram_link_token(token: str) -> int | None:
    if not token or not token.startswith(_TOKEN_PREFIX):
        return None

    try:
        raw = _b64_decode(token[len(_TOKEN_PREFIX) :])
    except Exception:
        return None

    payload_size = struct.calcsize(">BIII")
    if len(raw) != payload_size + _SIGNATURE_BYTES:
        return None

    payload = raw[:payload_size]
    signature = raw[payload_size:]
    expected_signature = hmac.new(_secret(), payload, hashlib.sha256).digest()[:_SIGNATURE_BYTES]
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        version, user_id, expires_at, _nonce = struct.unpack(">BIII", payload)
    except struct.error:
        return None

    if version != _TOKEN_VERSION or expires_at < int(time.time()):
        return None
    return user_id
