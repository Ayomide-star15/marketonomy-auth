# app/schemas/business_profile.py
#
# Same rule as before: this defines the JSON shape going in/out of the API.
# It's NOT the same thing as the database model — the Request schema only
# has fields the business owner is allowed to send; id/user_id/created_at
# are decided by the server, never trusted from the client.

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.business_profile import BusinessProfileStatusEnum


# ===== STEP 1 — CREATE / UPDATE BUSINESS PROFILE =====
# What the frontend sends when the business owner submits Step 1 of the
# wizard. Notice there's no user_id here — that comes from the logged-in
# user's JWT token in the endpoint, exactly like client_id does on the
# projects side.
class BusinessProfileRequest(BaseModel):
    org_name: str                              # "Business Name" — required on the form
    trading_name: Optional[str] = None         # optional field
    business_type: str                         # required dropdown
    industry: str                               # required dropdown
    year_established: int                      # required
    employee_count: Optional[str] = None        # dropdown, e.g. "6-20"
    bio: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None


# ===== RESPONSE — what gets sent back after creating/fetching a profile =====
class BusinessProfileResponse(BaseModel):
    id: str
    user_id: str
    org_name: Optional[str] = None
    trading_name: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    year_established: Optional[int] = None
    employee_count: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    status: str  # draft | pending_review | approved | rejected | suspended
    rejection_reason: Optional[str] = None
    created_at: datetime


    @field_validator("id", "user_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value
 

    class Config:
        # Lets Pydantic build this response directly from a SQLAlchemy
        # BusinessProfile object, instead of requiring a plain dict.
        from_attributes = True
# ===== ADMIN — APPROVE / REJECT A BUSINESS =====
# What the admin sends when reviewing a submission. Only ever used on
# admin-only endpoints — never exposed to the business owner themselves.
class BusinessReviewDecisionRequest(BaseModel):
    reason: Optional[str] = None   # required in practice for rejections, optional for approvals

    @field_validator("reason")
    @classmethod
    def reason_not_blank_if_provided(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Reason cannot be blank if provided")
        return value