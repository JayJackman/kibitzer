"""FastAPI dependencies injected into route handlers.

Dependencies are functions that FastAPI calls automatically before your
route handler runs. They provide shared resources (like a database session)
or enforce requirements (like "user must be logged in").

Usage in a route:
    @router.get("/me")
    def me(user: User = Depends(get_current_user)):
        return user
"""

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth.jwt import decode_token
from .auth.models import User
from .auth.service import get_user_by_username
from .config import ACCESS_TOKEN_COOKIE
from .db import get_db


def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
) -> User:
    """Extract the current user from the access_token cookie.

    FastAPI calls this automatically for any route that declares
    `user: User = Depends(get_current_user)`.

    Raises 401 if the cookie is missing, expired, or the user doesn't exist.
    """
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Decode the JWT and extract the username
    username = decode_token(access_token, expected_type="access")
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
