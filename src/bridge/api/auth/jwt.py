"""JWT token creation and decoding.

Two token types:
- "access"  -- short-lived (15 min), sent with every API request via cookie
- "refresh" -- long-lived (7 days), used only to get a new access token

Both are signed with the same secret key using HS256.
"""

from datetime import UTC, datetime, timedelta
from typing import Literal, TypedDict

from authlib.jose import JsonWebToken  # type: ignore[import-untyped]
from authlib.jose.errors import JoseError  # type: ignore[import-untyped]

from bridge.api.config import settings

_jwt = JsonWebToken(["HS256"])


class TokenPayload(TypedDict):
    """The claims we embed in every JWT we issue."""

    sub: str  # username
    exp: datetime  # expiration time
    type: Literal["access", "refresh"]


def create_access_token(username: str) -> str:
    """Create a short-lived access token for the given user."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: TokenPayload = {"sub": username, "exp": expire, "type": "access"}
    token: bytes = _jwt.encode({"alg": "HS256"}, payload, settings.secret_key)
    return token.decode()


def create_refresh_token(username: str) -> str:
    """Create a long-lived refresh token for the given user."""
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload: TokenPayload = {"sub": username, "exp": expire, "type": "refresh"}
    token: bytes = _jwt.encode({"alg": "HS256"}, payload, settings.secret_key)
    return token.decode()


def decode_token(token: str, expected_type: str) -> str | None:
    """Decode a JWT and return the username if valid.

    Returns None if the token is expired, malformed, or the wrong type
    (e.g., a refresh token used as an access token).
    """
    try:
        payload = _jwt.decode(token, settings.secret_key)
        # Validate expiration (authlib doesn't auto-reject expired tokens)
        payload.validate()
    except (JoseError, ValueError):
        return None

    # Check that the token type matches what we expect
    if payload.get("type") != expected_type:
        return None

    return payload.get("sub")  # type: ignore[no-any-return]
