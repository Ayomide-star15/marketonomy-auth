from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone

from app.models.session import Session
from app.services.auth_service import log_action


def logout_user(db: DBSession, user_id, jwt_token: str) -> bool:
    """Deactivate the current session so the token can't be reused"""

    session = (
        db.query(Session)
        .filter(Session.user_id == user_id)
        .filter(Session.jwt_token == jwt_token)
        .filter(Session.is_active == True)
        .first()
    )

    if session:
        session.is_active = False
        db.commit()

    log_action(db, user_id, "logout")

    return True


def get_active_sessions(db: DBSession, user_id) -> list:
    """Get all active sessions for a user - useful for 'logged in devices' feature"""

    sessions = (
        db.query(Session)
        .filter(Session.user_id == user_id)
        .filter(Session.is_active == True)
        .filter(Session.expires_at > datetime.now(timezone.utc))
        .all()
    )

    return sessions


def revoke_session(db: DBSession, user_id, session_id) -> bool:
    """Let user log out a specific device remotely"""

    session = (
        db.query(Session)
        .filter(Session.id == session_id)
        .filter(Session.user_id == user_id)
        .first()
    )

    if not session:
        raise ValueError("Session not found")

    session.is_active = False
    db.commit()

    return True