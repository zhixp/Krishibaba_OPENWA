"""
Shared security helpers for protected Krishi Baba backend surfaces.
"""
import hashlib
import re
from secrets import compare_digest
from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import settings


_WEAK_SECRET_VALUES = {
    "",
    "changeme",
    "changeme_in_production",
    "change_this_to_secure_random_key",
    "change_this_to_secure_random_channel_secret",
    "change_this_to_secure_random_salt",
    "sarpanch_secret",
    "your_admin_api_key_here",
    "your_channel_gateway_secret_here",
}
_MIN_SECRET_LENGTH = 24
_SAFE_TOKEN_RE = re.compile(r"[^A-Za-z0-9_.@+-]+")


def _is_weak_secret(secret: Optional[str]) -> bool:
    value = (secret or "").strip()
    return len(value) < _MIN_SECRET_LENGTH or value.lower() in _WEAK_SECRET_VALUES


def _require_strong_secret(secret: str, setting_name: str) -> str:
    if _is_weak_secret(secret):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{setting_name} is not configured securely",
        )
    return secret.strip()


def _verify_secret(provided: Optional[str], configured: str, setting_name: str) -> str:
    expected = _require_strong_secret(configured, setting_name)
    candidate = (provided or "").strip()

    if not candidate or not compare_digest(candidate, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return candidate


def verify_admin_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify the shared admin API key from the X-API-Key header."""
    return _verify_secret(x_api_key, settings.ADMIN_API_KEY, "ADMIN_API_KEY")


def verify_broadcast_admin_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Verify broadcast access, falling back to the shared admin key if unset."""
    configured = settings.BROADCAST_ADMIN_KEY or settings.ADMIN_API_KEY
    setting_name = "BROADCAST_ADMIN_KEY" if settings.BROADCAST_ADMIN_KEY else "ADMIN_API_KEY"
    return _verify_secret(x_api_key, configured, setting_name)


def verify_channel_gateway_secret(x_channel_secret: Optional[str] = Header(None)) -> str:
    """Verify the OpenWA gateway secret from the X-Channel-Secret header."""
    return _verify_secret(x_channel_secret, settings.CHANNEL_GATEWAY_SECRET, "CHANNEL_GATEWAY_SECRET")


def safe_storage_token(value: str, fallback: str = "user", max_length: int = 80) -> str:
    """Return a filesystem-safe token for user-controlled identifiers."""
    cleaned = _SAFE_TOKEN_RE.sub("_", (value or "").strip()).strip("._-")
    return (cleaned or fallback)[:max_length]


def redacted_identifier(value: str) -> str:
    """Stable short hash for logs without exposing farmer identifiers."""
    digest = hashlib.sha256((value or "").encode("utf-8")).hexdigest()
    return digest[:10]
