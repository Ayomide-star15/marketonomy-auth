from sqlalchemy.orm import Session as DBSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime, timezone, timedelta

from app.models.user import User, RoleEnum, AuthProviderEnum
from app.models.session import Session
from app.models.login_attempt import LoginAttempt
from app.models.account_lockout import AccountLockout
from app.models.audit_log import AuditLog
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings


def verify_google_token(google_token: str) -> dict:
    """Verify the Google token and return user info"""
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        return {
            "google_id": idinfo["sub"],
            "email": idinfo["email"],
            "first_name": idinfo.get("given_name"),
            "last_name": idinfo.get("family_name"),
            "profile_photo": idinfo.get("picture"),
            "email_verified": idinfo.get("email_verified", False),
        }
    except Exception as e:
        raise ValueError(f"Invalid Google token: {str(e)}")


def google_signup(db: DBSession, google_token: str, role: str) -> User:
    """Handle Google signup - create new user or return existing one"""

    # Step 1 - Verify the Google token
    google_data = verify_google_token(google_token)

    if not google_data["email_verified"]:
        raise ValueError("Google email is not verified")

    # Step 2 - Check if user already exists
    existing_user = db.query(User).filter(User.email == google_data["email"]).first()

    if existing_user:
        return existing_user

    # Step 3 - Validate role
    if role not in [RoleEnum.client.value, RoleEnum.business_owner.value]:
        raise ValueError("Role must be 'client' or 'business_owner'")

    # Step 4 - Create new user
    new_user = User(
        email=google_data["email"],
        google_id=google_data["google_id"],
        first_name=google_data["first_name"],
        last_name=google_data["last_name"],
        profile_photo=google_data["profile_photo"],
        role=role,
        is_email_verified=True,
        has_set_password=False,
        auth_provider=AuthProviderEnum.google,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Step 5 - Log this action
    log_action(db, new_user.id, "google_signup")

    return new_user


def google_login(db: DBSession, google_token: str) -> User:
    """Handle Google login for existing users"""

    google_data = verify_google_token(google_token)

    user = db.query(User).filter(User.email == google_data["email"]).first()

    if not user:
        raise ValueError("No account found with this email. Please sign up first.")

    if user.status != "active":
        raise ValueError(f"Account is {user.status}. Please contact support.")

    update_last_login(db, user)
    log_action(db, user.id, "google_login")

    return user


def login_with_password(
    db: DBSession,
    email: str,
    password: str,
    ip_address: str = None,
    device_info: str = None,
) -> User:
    """Handle email + password login"""

    user = db.query(User).filter(User.email == email).first()

    # Check account lockout first
    check_account_lockout(db, email)

    if not user:
        record_login_attempt(db, email, ip_address, device_info, "failed", "email_not_found")
        raise ValueError("Invalid email or password")

    if not user.has_set_password or not user.password_hash:
        record_login_attempt(db, email, ip_address, device_info, "failed", "password_not_set")
        raise ValueError("Please sign up with Google and set a password first")

    if not verify_password(password, user.password_hash):
        record_login_attempt(db, email, ip_address, device_info, "failed", "wrong_password")
        check_and_lock_account(db, email)
        raise ValueError("Invalid email or password")

    if user.status != "active":
        record_login_attempt(db, email, ip_address, device_info, "failed", f"account_{user.status}")
        raise ValueError(f"Account is {user.status}. Please contact support.")

    # Success
    record_login_attempt(db, email, ip_address, device_info, "success", None)
    update_last_login(db, user)
    log_action(db, user.id, "login", ip_address, device_info)

    return user


def generate_tokens_for_user(
    db: DBSession,
    user: User,
    ip_address: str = None,
    device_info: str = None,
) -> dict:
    """Create access + refresh tokens and save session"""

    token_data = {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Save session
    session = Session(
        user_id=user.id,
        jwt_token=access_token,
        ip_address=ip_address,
        device_info=device_info,
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    db.add(session)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def update_last_login(db: DBSession, user: User):
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()


def log_action(db: DBSession, user_id, action: str, ip_address: str = None, device_info: str = None):
    audit = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        device_info=device_info,
    )
    db.add(audit)
    db.commit()


def record_login_attempt(
    db: DBSession,
    email: str,
    ip_address: str,
    device_info: str,
    status: str,
    failure_reason: str = None,
):
    attempt = LoginAttempt(
        email=email,
        ip_address=ip_address,
        device_info=device_info,
        status=status,
        failure_reason=failure_reason,
    )
    db.add(attempt)
    db.commit()


def check_account_lockout(db: DBSession, email: str):
    """Raise error if account is currently locked"""
    lockout = (
        db.query(AccountLockout)
        .filter(AccountLockout.email == email)
        .filter(AccountLockout.locked_until > datetime.now(timezone.utc))
        .order_by(AccountLockout.created_at.desc())
        .first()
    )
    if lockout:
        raise ValueError(f"Account is locked until {lockout.locked_until}. Too many failed attempts.")


def check_and_lock_account(db: DBSession, email: str):
    """Lock account after 5 failed attempts in the last 15 minutes"""

    fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)

    failed_attempts = (
        db.query(LoginAttempt)
        .filter(LoginAttempt.email == email)
        .filter(LoginAttempt.status == "failed")
        .filter(LoginAttempt.attempted_at >= fifteen_min_ago)
        .count()
    )

    if failed_attempts >= 5:
        user = db.query(User).filter(User.email == email).first()
        lockout = AccountLockout(
            user_id=user.id if user else None,
            email=email,
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=30),
            reason="Too many failed login attempts",
        )
        db.add(lockout)
        db.commit()