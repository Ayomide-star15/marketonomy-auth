from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.schemas.token import RefreshTokenRequest, RefreshTokenResponse, VerifyTokenResponse
from app.services.token_service import verify_token, refresh_access_token
from app.db.database import get_db
from sqlalchemy.orm import Session as DBSession

router = APIRouter(prefix="/auth", tags=["Token"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.get("/verify-token", response_model=VerifyTokenResponse)
def verify_token_endpoint(token: str = Depends(oauth2_scheme)):
    """
    This is the endpoint Eric's API can call (or just decode 
    the JWT himself using the shared secret - Option B we discussed)
    """
    try:
        result = verify_token(token)
        return VerifyTokenResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh-token", response_model=RefreshTokenResponse)
def refresh_token_endpoint(data: RefreshTokenRequest, db: DBSession = Depends(get_db)):
    try:
        result = refresh_access_token(db, data.refresh_token)
        return RefreshTokenResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))