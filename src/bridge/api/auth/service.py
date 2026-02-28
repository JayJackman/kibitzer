"""Auth business logic: password hashing, user creation, authentication.

This module contains the "how" of auth -- the router (router.py) handles
the "when" (HTTP endpoints) and delegates here for the actual work.
"""

import bcrypt
from sqlalchemy.orm import Session

from .models import User


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def get_user_by_username(db: Session, username: str) -> User | None:
    """Look up a user by username (case-insensitive). Returns None if not found."""
    return db.query(User).filter(User.username.ilike(username)).first()


def create_user(db: Session, username: str, password: str) -> User:
    """Create a new user with a hashed password.

    Caller should check for duplicate usernames first (or handle the
    IntegrityError from the unique constraint).
    """
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Verify credentials. Returns the User if valid, None otherwise."""
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
