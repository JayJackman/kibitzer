"""FastAPI dependencies injected into route handlers.

Dependencies are functions that FastAPI calls automatically before your
route handler runs. They provide shared resources (like a database session)
or enforce requirements (like "user must be logged in").

Usage in a route:
    @router.get("/me")
    def me(user: User = Depends(get_current_user)):
        return user
"""

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .auth.jwt import decode_token
from .auth.models import User
from .auth.service import get_user_by_username
from .config import ACCESS_TOKEN_COOKIE
from .db import get_db


def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    authorization: str | None = Header(default=None),
) -> User:
    """Extract the current user from a Bearer token or cookie.

    Checks the Authorization header first (for iOS/mobile clients),
    then falls back to the access_token cookie (for the web app).

    FastAPI calls this automatically for any route that declares
    `user: User = Depends(get_current_user)`.

    Raises 401 if no valid token is found or the user doesn't exist.
    """
    # Try Bearer token first (iOS), then cookie (web)
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif access_token:
        token = access_token

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Decode the JWT and extract the username
    username = decode_token(token, expected_type="access")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Look up the user in the database
    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
