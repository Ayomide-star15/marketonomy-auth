from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.schemas.auth import (
    GoogleSignupRequest,
    GoogleSignupResponse,
    GoogleLoginRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
)
from app.services.auth_service import (
    google_signup,
    google_login,
    login_with_password,
    generate_tokens_for_user,
)
from app.services.password_service import create_password_set_token
from app.services.session_service import logout_user
from app.services.email_service import send_welcome_email
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/google-signup", response_model=GoogleSignupResponse)
def signup_with_google(data: GoogleSignupRequest, db: DBSession = Depends(get_db)):
    try:
        user = google_signup(db, data.google_token, data.role)

        # Create a password_set_token so frontend knows user needs to set password
        if not user.has_set_password:
            create_password_set_token(db, user.id)
            send_welcome_email(user.email, user.first_name or "there")

        return GoogleSignupResponse(
            message="Account created successfully",
            user_id=str(user.id),
            role=user.role.value if hasattr(user.role, "value") else user.role,
            has_set_password=user.has_set_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/google-login", response_model=LoginResponse)
def login_with_google(data: GoogleLoginRequest, request: Request, db: DBSession = Depends(get_db)):
    try:
        user = google_login(db, data.google_token)

        tokens = generate_tokens_for_user(
            db, user,
            ip_address=request.client.host if request.client else None,
            device_info=request.headers.get("user-agent"),
        )

        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=str(user.id),
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else user.role,
            first_name=user.first_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, request: Request, db: DBSession = Depends(get_db)):
    try:
        user = login_with_password(
            db, data.email, data.password,
            ip_address=request.client.host if request.client else None,
            device_info=request.headers.get("user-agent"),
        )

        tokens = generate_tokens_for_user(
            db, user,
            ip_address=request.client.host if request.client else None,
            device_info=request.headers.get("user-agent"),
        )

        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=str(user.id),
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else user.role,
            first_name=user.first_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=LogoutResponse)
def logout(
    data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    # Note: we use the access token from the Authorize header to identify the session
    from fastapi import Request as FastAPIRequest
    logout_user(db, current_user.id, data.refresh_token)
    return LogoutResponse(message="Logged out successfully")