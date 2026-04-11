"""Pydantic schemas for auth request/response bodies.

These are the shapes of JSON that the API sends and receives -- separate
from the SQLAlchemy model (which maps to the database row).
"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """POST /api/auth/register request body."""

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    """POST /api/auth/login request body."""

    username: str
    password: str


class UserResponse(BaseModel):
    """User info returned by GET /api/auth/me."""

    id: int
    username: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Response from login/register — includes JWT tokens for mobile clients.

    The web app ignores the token fields and uses httpOnly cookies instead.
    The iOS app reads these tokens and sends them as Bearer headers.
    """

    id: int
    username: str
    access_token: str
    refresh_token: str

    model_config = {"from_attributes": False}


class RefreshRequest(BaseModel):
    """POST /api/auth/refresh request body (for mobile clients).

    Web clients send the refresh token via cookie automatically.
    Mobile clients send it in the request body instead.
    """

    refresh_token: str | None = None


class RefreshResponse(BaseModel):
    """Response from /api/auth/refresh — includes the new access token."""

    message: str
    access_token: str


class MessageResponse(BaseModel):
    """Generic success message (e.g., logout confirmation)."""

    message: str
