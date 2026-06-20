from pydantic import BaseModel
from typing import Optional


# ===== REFRESH TOKEN (get new access token) =====
class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ===== VERIFY TOKEN (what Eric's API will use) =====
class VerifyTokenResponse(BaseModel):
    user_id: str
    email: str
    role: str
    is_valid: bool = True


# ===== DECODED TOKEN DATA (used internally) =====
class TokenPayload(BaseModel):
    user_id: str
    email: str
    role: str
    exp: Optional[int] = None