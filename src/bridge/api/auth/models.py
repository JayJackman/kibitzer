"""SQLAlchemy model for user accounts."""

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from bridge.api.db import Base


class User(Base):
    """A registered user account.

    Passwords are stored as bcrypt hashes (see auth/service.py).
    The username is unique and used as the JWT subject claim.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
