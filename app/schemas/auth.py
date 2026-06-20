from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ===== GOOGLE SIGNUP =====
class GoogleSignupRequest(BaseModel):
    google_token: str
    role: str  # "client" or "business_owner"


class GoogleSignupResponse(BaseModel):
    message: str
    user_id: str
    role: str
    has_set_password: bool


# ===== GOOGLE LOGIN (for users who already exist) =====
class GoogleLoginRequest(BaseModel):
    google_token: str


# ===== EMAIL + PASSWORD LOGIN =====
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    full_name: Optional[str] = None


# ===== LOGOUT =====
class LogoutRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    message: str


# ===== USER PROFILE (returned after login/signup) =====
class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_photo: Optional[str] = None
    role: str
    status: str
    is_email_verified: bool
    has_set_password: bool
    created_at: datetime

    class Config:
        from_attributes = True