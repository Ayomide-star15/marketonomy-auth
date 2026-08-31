# app/schemas/business_document.py

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID

from app.models.business_document import DocumentTypeEnum


class BusinessDocumentUploadRequest(BaseModel):
    document_type: str
    expiry_date: Optional[date] = None

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        valid_types = [t.value for t in DocumentTypeEnum]
        if value not in valid_types:
            raise ValueError(f"document_type must be one of: {', '.join(valid_types)}")
        return value


class BusinessDocumentResponse(BaseModel):
    id: str
    business_profile_id: str
    document_type: str
    document_name: str
    status: str                              # pending | verified | rejected
    rejection_reason: Optional[str] = None
    expiry_date: Optional[date] = None
    file_size: Optional[int] = None
    uploaded_at: datetime

    # document_url deliberately excluded — internal storage path only,
    # use the download-url endpoint to actually view the file.

    @field_validator("id", "business_profile_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True


class DocumentDownloadUrlResponse(BaseModel):
    download_url: str
    expires_in_seconds: int


class RequiredDocumentsStatusResponse(BaseModel):
    total_required: int
    completed: int
    missing: list[str]


# ===== ADMIN — approve/reject a SPECIFIC document =====
# Only ever used on admin-only endpoints — never exposed to the
# business owner. Same pattern as BusinessReviewDecisionRequest for
# whole-profile rejection, but scoped to one document.
class DocumentReviewDecisionRequest(BaseModel):
    reason: Optional[str] = None   # required in practice for rejections

    @field_validator("reason")
    @classmethod
    def reason_not_blank_if_provided(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Reason cannot be blank if provided")
        return value