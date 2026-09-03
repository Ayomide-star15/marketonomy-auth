# app/models/business_bank_details.py
#
# Typed verification data — NOT file uploads. Bank Details is entirely
# typed fields. NIN is a typed number here; the matching hard-copy PHOTO
# lives separately in business_documents (document_type='nin_document').
# One business has exactly one row here (enforced by a unique constraint
# on business_profile_id), same 1:1 rule as business_profiles <-> users.

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class BusinessBankDetails(Base):
    __tablename__ = "business_bank_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_profile_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Bank Details — typed only, no file
    bank_name = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_number = Column(String(50), nullable=False)

    # NIN — the number itself. The physical card/slip photo is a
    # separate BusinessDocument row (document_type='nin_document').
    nin_number = Column(String(20), nullable=False)

    is_verified = Column(Boolean, default=False)   # admin-only, never business-owner-settable

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())