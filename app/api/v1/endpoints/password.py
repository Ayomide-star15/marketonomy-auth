from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.schemas.password import (
    SetPasswordRequest,
    SetPasswordResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.services.password_service import set_password, request_password_reset, reset_password
from app.services.auth_service import generate_tokens_for_user
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Password"])


@router.post("/set-password", response_model=SetPasswordResponse)
def set_password_endpoint(
    data: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    try:
        user = set_password(db, current_user.id, data.password)
        tokens = generate_tokens_for_user(db, user)

        return SetPasswordResponse(
            message="Password set successfully",
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            role=user.role.value if hasattr(user.role, "value") else user.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: DBSession = Depends(get_db)):
    request_password_reset(db, data.email)
    return ForgotPasswordResponse(
        message="If an account exists with this email, a reset link has been sent"
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password_endpoint(data: ResetPasswordRequest, db: DBSession = Depends(get_db)):
    try:
        reset_password(db, data.token, data.new_password)
        return ResetPasswordResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))