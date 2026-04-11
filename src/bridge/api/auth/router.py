"""Auth API endpoints: register, login, logout, refresh, me.

Auth supports two transports:
- **Cookies** (web app): httpOnly cookies set automatically, more secure
  against XSS since JavaScript can't read them.
- **Bearer tokens** (iOS app): tokens returned in the response body,
  stored in Keychain, sent via Authorization header on each request.

Both transports use the same JWT tokens with the same signing key.
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
from .schemas import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    UserResponse,
)
from .service import authenticate_user, create_user, get_user_by_username

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookies(response: Response, username: str) -> tuple[str, str]:
    """Set both access and refresh token cookies on the response.

    Also returns the raw token strings so they can be included in the
    response body for mobile clients (which use Bearer tokens instead
    of cookies).

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

    return access_token, refresh_token


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Create a new user account and log them in immediately.

    Returns user info + JWT tokens in the response body (for mobile
    clients) and also sets httpOnly cookies (for web clients).
    """
    # Check if username is already taken
    if get_user_by_username(db, body.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = create_user(db, body.username, body.password)
    access_token, refresh_token = _set_auth_cookies(response, user.username)

    return AuthResponse(
        id=user.id,
        username=user.username,
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Authenticate with username/password and receive auth tokens.

    Returns user info + JWT tokens in the response body (for mobile
    clients) and also sets httpOnly cookies (for web clients).
    """
    user = authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token, refresh_token = _set_auth_cookies(response, user.username)

    return AuthResponse(
        id=user.id,
        username=user.username,
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    """Clear auth cookies to log the user out.

    No authentication required -- if the cookies don't exist, this is a
    harmless no-op.
    """
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path=REFRESH_TOKEN_PATH)
    return MessageResponse(message="Logged out")


@router.post("/refresh", response_model=RefreshResponse)
def refresh(
    response: Response,
    body: RefreshRequest | None = None,
    refresh_token_cookie: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
) -> RefreshResponse:
    """Exchange a valid refresh token for a new access token.

    Accepts the refresh token from either:
    - The request body (mobile clients): {"refresh_token": "..."}
    - A cookie (web clients): automatically sent by the browser

    Returns the new access token in the response body (for mobile) and
    also sets it as a cookie (for web).
    """
    # Try request body first (mobile), then cookie (web)
    token = (
        body.refresh_token if body and body.refresh_token else None
    ) or refresh_token_cookie

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    username = decode_token(token, expected_type="refresh")
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

    return RefreshResponse(message="Token refreshed", access_token=new_access)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user's info.

    This endpoint is how the frontend checks "am I logged in?" on page
    load. If the access token cookie is valid, it returns user info.
    If not, it returns 401 (handled by the get_current_user dependency).
    """
    return user
