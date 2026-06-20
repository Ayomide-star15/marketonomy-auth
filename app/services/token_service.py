from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.models.token import RefreshToken
from app.core.security import create_access_token, decode_token
from app.core.config import settings


def verify_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.
    This is what Eric's API will essentially replicate
    using the same JWT_SECRET.
    """
    try:
        payload = decode_token(token)
        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "is_valid": True,
        }
    except ValueError:
        raise ValueError("Invalid or expired token")


def refresh_access_token(db: DBSession, refresh_token: str) -> dict:
    """
    Given a valid refresh token, issue a new access token
    without requiring the user to log in again.
    """
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise ValueError("Invalid or expired refresh token")

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise ValueError("User not found")

    if user.status != "active":
        raise ValueError(f"Account is {user.status}")

    new_access_token = create_access_token({
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
    })

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }