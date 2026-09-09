# app/models/guarantor.py
#
# One table, two purposes — contact_type distinguishes "next_of_kin"
# from "guarantor" (matches Step 5 of the wizard, which has both
# sections). Note this is keyed to user_id, NOT business_profile_id —
# different from business_documents/business_bank_details, but that's
# how the live DB table is actually built, so we match it as-is.

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class ContactTypeEnum(str, enum.Enum):
    guarantor = "guarantor"
    next_of_kin = "next_of_kin"


class Guarantor(Base):
    __tablename__ = "guarantors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    contact_type = Column(String(50), nullable=False, default=ContactTypeEnum.guarantor.value)

    full_name = Column(String(255), nullable=False)
    relationship = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    employer = Column(String(255), nullable=True)   # "Workplace" on the guarantor form / occupation-adjacent
    job_title = Column(String(255), nullable=True)  # "Occupation" on the wizard form

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())