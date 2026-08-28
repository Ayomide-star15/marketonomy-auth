# app/api/v1/endpoints/business.py
#
# The API layer for the business side. This file is what your colleague
# will keep adding to as he builds business_documents, business_interviews,
# etc. — same router, more endpoints appended below over time.
#
# Same pattern as projects.py: thin functions, real logic lives in
# business_profile_service.py.

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.schemas.business_profile import(
    BusinessProfileRequest,
    BusinessProfileResponse
)

from app.services.business_profile_service import (
    create_or_update_business_profile,
    get_my_business_profile,
    get_business_profile_by_id,
)
from app.core.dependencies import get_current_user, require_role   # same JWT dependency used everywhere else
from app.models.user import User

# prefix="/business" means every route below lives at /api/v1/business/...
# once this router is registered in main.py.
router = APIRouter(prefix="/business", tags=["Business"])


@router.post("/profile", response_model=BusinessProfileResponse)
def save_business_profile(
    data: BusinessProfileRequest,
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    """
    POST /api/v1/business/profile
    Step 1 of the registration wizard. Creates the profile the first time,
    updates it on any later call — so this same endpoint covers both
    "first submit" and "come back and edit" without needing two endpoints.
    """
    profile = create_or_update_business_profile(
        db,
        user_id=current_user.id,
        data=data.model_dump(),   # turns the Pydantic schema into a plain dict for the service layer
    )
    return profile


@router.get("/profile/me", response_model=BusinessProfileResponse)
def get_my_profile(
    current_user: User =  Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    """
    GET /api/v1/business/profile/me
    Used to pre-fill Step 1 if the business owner is returning to edit
    their profile instead of creating it for the first time.
    """
    try:
        return get_my_business_profile(db, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/profile/{business_id}", response_model=BusinessProfileResponse)
def get_profile_by_id(
    business_id: UUID,
    db: DBSession = Depends(get_db),
):
    """
    GET /api/v1/business/profile/{business_id}
    Public endpoint — any client can view an approved business profile by ID.
    Returns 404 if the business does not exist or has not been approved.
    """
    try:
        return get_business_profile_by_id(db, business_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))