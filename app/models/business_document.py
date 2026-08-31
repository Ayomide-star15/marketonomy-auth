# app/models/business_document.py
#
# One row per uploaded FILE document — Business Registration, Tax ID,
# Owner ID, and the NIN hard-copy photo. Bank Details + the NIN number
# itself live separately in business_bank_details (typed data, no file).

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class DocumentTypeEnum(str, enum.Enum):
    """Mirrors business_documents.document_type CHECK constraint exactly."""
    business_registration = "business_registration"
    tax_identification = "tax_identification"
    owner_id = "owner_id"
    nin_document = "nin_document"
    other = "other"


class DocumentStatusEnum(str, enum.Enum):
    """
    Mirrors business_documents.status CHECK constraint exactly.
    Per-document review status — separate from business_profiles.status,
    since admin needs to reject ONE document (e.g. an expired Tax ID
    certificate) without rejecting the whole business profile.
    """
    pending = "pending"      # default — uploaded, not yet reviewed by admin
    verified = "verified"    # admin confirmed this specific document is valid
    rejected = "rejected"    # admin rejected this specific document, see rejection_reason


class BusinessDocument(Base):
    __tablename__ = "business_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    business_profile_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False)

    document_type = Column(String(50), nullable=False)   # plain String — DB column is text + CHECK

    document_name = Column(String(255), nullable=False)   # original filename
    document_url = Column(String(500), nullable=False)    # Supabase Storage path — bucket is private,
                                                             # view via signed URL only

    expiry_date = Column(Date, nullable=True)
    file_size = Column(Integer, nullable=True)

    # Per-document review status, admin-only to change — never in the
    # business owner's request schema.
    status = Column(String(50), nullable=False, default=DocumentStatusEnum.pending.value)
    rejection_reason = Column(String(255), nullable=True)   # set when status='rejected'

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())