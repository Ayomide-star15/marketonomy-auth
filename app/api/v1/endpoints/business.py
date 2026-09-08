# app/api/v1/endpoints/business.py
#
# The API layer for the business side. This file is what your colleague
# will keep adding to as he builds business_documents, business_interviews,
# etc. — same router, more endpoints appended below over time.
#
# Same pattern as projects.py: thin functions, real logic lives in
# business_profile_service.py.

from uuid import UUID

from fastapi import (
    APIRouter, 
    Depends,
    HTTPException, 
    status, 
    UploadFile, 
    File, 
    Form
)

from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
from datetime import date

from app.db.database import get_db

from app.schemas.business_profile import(
    BusinessProfileRequest,
    BusinessProfileResponse
)

from app.schemas.business_document import(
    BusinessDocumentResponse,
    DocumentDownloadUrlResponse,
    RequiredDocumentsStatusResponse
)

from app.services.business_document_service import (
    upload_business_document,
    get_my_documents,
    get_document_download_url,
    delete_document,
    get_required_documents_status,
)


from app.services.business_profile_service import (
    create_or_update_business_profile,
    get_my_business_profile,
    get_business_profile_by_id,
    
)

from app.schemas.business_bank_details import (
    BusinessBankDetailsRequest, 
    BusinessBankDetailsResponse,
    BusinessBankDetailsUpdateRequest
)

from app.services.business_bank_details_service import (
    create_or_update_bank_details, 
    get_my_bank_details,
    update_bank_details_partial
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


# ===== FILE DOCUMENTS =====

@router.post("/documents", response_model=BusinessDocumentResponse)
def upload_document(
    document_type: str = Form(...),
    expiry_date: Optional[date] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    """
    POST /api/v1/business/documents
    multipart/form-data. document_type must be one of:
    business_registration | tax_identification | owner_id | nin_document | other
    """
    try:
        return upload_business_document(
            db, user_id=current_user.id, document_type=document_type,
            file=file, expiry_date=expiry_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/documents", response_model=List[BusinessDocumentResponse])
def list_my_documents(
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    return get_my_documents(db, current_user.id)


@router.get("/documents/{document_id}/download-url", response_model=DocumentDownloadUrlResponse)
def get_download_url(
    document_id: str,
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    try:
        url = get_document_download_url(db, current_user.id, document_id)
        return DocumentDownloadUrlResponse(download_url=url, expires_in_seconds=300)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/documents/{document_id}")
def remove_document(
    document_id: str,
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    try:
        delete_document(db, current_user.id, document_id)
        return {"message": "Document deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/documents/required-status", response_model=RequiredDocumentsStatusResponse)
def get_documents_progress(
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    """Powers the '0/5 uploaded' progress badge in the wizard sidebar."""
    profile = get_my_business_profile(db, current_user.id)
    return get_required_documents_status(db, profile.id)

# ===== BANK DETAILS =====

@router.post("/bank-details", response_model=BusinessBankDetailsResponse)
def save_bank_details(
    data: BusinessBankDetailsRequest,
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    """
    POST /api/v1/business/bank-details
    Business owner submits their bank details and NIN for the first time.
    If details already exist, this updates them instead — same upsert
    pattern used across the rest of the business registration wizard.
    """
    try:
        return create_or_update_bank_details(db, user_id=current_user.id, data=data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/bank-details", response_model=BusinessBankDetailsResponse)
def get_bank_details(
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    """
    GET /api/v1/business/bank-details
    Business owner fetches their existing bank details to pre-fill the form
    if they're returning to edit rather than submitting for the first time.
    """
    try:
        return get_my_bank_details(db, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/bank-details", response_model=BusinessBankDetailsResponse)
def update_bank_details(
    data: BusinessBankDetailsRequest,
    current_user: User = Depends(require_role("business_owner")),
    db: DBSession = Depends(get_db),
):
    """
    PATCH /api/v1/business/bank-details
    Business owner updates their existing bank details.
    Uses the same upsert service function — if no record exists yet,
    it creates one; if it does, it updates it.
    """
    try:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")
        return update_bank_details_partial(db, user_id=current_user.id, data=update_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))