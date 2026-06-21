from pydantic import BaseModel, EmailStr, field_validator
import re


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password is too long (maximum 72 characters)")
    if not any(char.isupper() for char in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(char.islower() for char in value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(char.isdigit() for char in value):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]/~`]", value):
        raise ValueError("Password must contain at least one special character (e.g. !@#$%^&*)")
    return value


# ===== SET PASSWORD (after Google signup) =====
class SetPasswordRequest(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class SetPasswordResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    role: str


# ===== FORGOT PASSWORD =====
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


# ===== RESET PASSWORD =====
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class ResetPasswordResponse(BaseModel):
    message: str