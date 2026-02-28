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
    """User info returned by GET /api/auth/me and registration."""

    id: int
    username: str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic success message (e.g., logout confirmation)."""

    message: str
