"""Auth API endpoints: register, login, logout, refresh, me.

All auth state is managed via httpOnly cookies (not Authorization headers).
This is more secure for browser-based apps because JavaScript can't read
httpOnly cookies, preventing XSS attacks from stealing tokens.
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from bridge.api.config import (
    ACCESS_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
    REFRESH_TOKEN_PATH,
)
from bridge.api.db import get_db
from bridge.api.deps import get_current_user

from .jwt import create_access_token, create_refresh_token, decode_token
from .models import User
from .schemas import LoginRequest, MessageResponse, RegisterRequest, UserResponse
from .service import authenticate_user, create_user, get_user_by_username

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookies(response: Response, username: str) -> None:
    """Set both access and refresh token cookies on the response.

    httpOnly=True  -> JavaScript can't read the cookie (XSS protection)
    samesite="lax" -> Cookie sent on same-site requests and top-level
                      navigations (CSRF protection)
    secure=False   -> Allow HTTP in development. Set True in production
                      behind HTTPS.
    """
    access_token = create_access_token(username)
    refresh_token = create_refresh_token(username)

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path=REFRESH_TOKEN_PATH,  # Only sent to the refresh endpoint
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    """Create a new user account and log them in immediately."""
    # Check if username is already taken
    if get_user_by_username(db, body.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = create_user(db, body.username, body.password)

    # Auto-login: set cookies so the user doesn't have to log in separately
    _set_auth_cookies(response, user.username)

    return user


@router.post("/login", response_model=UserResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    """Authenticate with username/password and receive auth cookies."""
    user = authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    _set_auth_cookies(response, user.username)
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    """Clear auth cookies to log the user out.

    No authentication required -- if the cookies don't exist, this is a
    harmless no-op.
    """
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path=REFRESH_TOKEN_PATH)
    return MessageResponse(message="Logged out")


@router.post("/refresh", response_model=MessageResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
) -> MessageResponse:
    """Exchange a valid refresh token for a new access token.

    The frontend calls this automatically when it gets a 401. The user
    never sees this happen -- their session just continues seamlessly.
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    username = decode_token(refresh_token, expected_type="refresh")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Issue a new access token (keep the existing refresh token)
    new_access = create_access_token(username)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=new_access,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

    return MessageResponse(message="Token refreshed")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user's info.

    This endpoint is how the frontend checks "am I logged in?" on page
    load. If the access token cookie is valid, it returns user info.
    If not, it returns 401 (handled by the get_current_user dependency).
    """
    return user
