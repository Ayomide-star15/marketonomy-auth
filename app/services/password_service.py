from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone, timedelta

from app.models.user import User, AuthProviderEnum
from app.models.token import PasswordSetToken, PasswordResetToken
from app.core.security import hash_password, generate_secure_token
from app.services.auth_service import log_action, generate_tokens_for_user
from app.services.email_service import send_password_reset_email


def create_password_set_token(db: DBSession, user_id) -> str:
    """Called right after Google signup - lets user set a password"""

    token = generate_secure_token()

    password_set_token = PasswordSetToken(
        user_id=user_id,
        token=token,
        is_used=False,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    db.add(password_set_token)
    db.commit()

    return token


def set_password(db: DBSession, user_id, new_password: str) -> User:
    """User sets their password after Google signup (called from inside dashboard)"""

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise ValueError("User not found")

    if user.has_set_password:
        raise ValueError("Password has already been set for this account")

    # Hash and save the password
    user.password_hash = hash_password(new_password)
    user.has_set_password = True
    user.auth_provider = AuthProviderEnum.both
    db.commit()

    log_action(db, user.id, "password_set")

    return user


def request_password_reset(db: DBSession, email: str) -> bool:
    """User forgot password - send them a reset link"""

    user = db.query(User).filter(User.email == email).first()

    # Don't reveal whether the email exists or not (security best practice)
    if not user:
        return True

    if not user.has_set_password:
        return True  # Can't reset a password that was never set

    token = generate_secure_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        is_used=False,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    db.add(reset_token)
    db.commit()

    send_password_reset_email(user.email, token)
    log_action(db, user.id, "password_reset_requested")

    return True


def reset_password(db: DBSession, token: str, new_password: str) -> User:
    """User clicks reset link and sets a new password"""

    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == token)
        .filter(PasswordResetToken.is_used == False)
        .first()
    )

    if not reset_token:
        raise ValueError("Invalid or already used reset token")

    if reset_token.expires_at < datetime.now(timezone.utc):
        raise ValueError("Reset token has expired. Please request a new one")

    user = db.query(User).filter(User.id == reset_token.user_id).first()

    if not user:
        raise ValueError("User not found")

    # Update password
    user.password_hash = hash_password(new_password)

    # Mark token as used
    reset_token.is_used = True

    db.commit()

    log_action(db, user.id, "password_reset_completed")

    return user