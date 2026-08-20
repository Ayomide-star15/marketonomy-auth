# app/models/business_profile.py
#
# This is the FOUNDATION table for the entire business side — almost every
# other business table (business_documents, business_interviews,
# business_verification, guarantors, business_track_record) has a foreign
# key pointing back to this table's id. Nothing else on the business side
# can really be tested until this one exists and works.
#
# It maps directly to Step 1 of the registration wizard: Business Name,
# Trading Name, Business Type, Industry, Year Established, Employees.

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class BusinessProfile(Base):
    __tablename__ = "business_profiles"  # must match the exact table name in Supabase

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which user account owns this business profile. One user can only
    # have one business profile (that's why this isn't a list anywhere) —
    # if you ever need multiple businesses per user, that's a bigger
    # schema change, not something to bolt on casually later.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # These first few match what was already in the table before this week.
    org_name = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # These 5 are the ones that needed adding via migration — CONFIRM these
    # columns actually exist in Supabase before running this code, or every
    # save will fail with a "column does not exist" error.
    trading_name = Column(String(255), nullable=True)      # optional, e.g. a DBA name
    business_type = Column(String(100), nullable=True)     # e.g. "LLC / Ltd", "Sole Proprietor"
    industry = Column(String(100), nullable=True)          # e.g. "SaaS & Tech" — also what Market's filter chips read from
    year_established = Column(Integer, nullable=True)      # feeds the Trust Score "Longevity" calculation later
    employee_count = Column(String(50), nullable=True)     # stored as text since it's a range label like "6-20", not a raw number

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())