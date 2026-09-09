# app/models/business_interview.py
#
# Step 6 of the wizard — the mandatory onboarding call before admin
# review. One business can have multiple rows over time (e.g. if a
# scheduled interview gets cancelled and rebooked), but only ever ONE
# row that's currently "scheduled" or "pending" at a time — enforced
# in the service layer.

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class InterviewStatusEnum(str, enum.Enum):
    pending = "pending"
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class InterviewTypeEnum(str, enum.Enum):
    virtual = "virtual"
    in_person = "in_person"
    phone = "phone"


class BusinessInterview(Base):
    __tablename__ = "business_interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_profile_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False)

    # Which admin/team member is assigned to conduct it — nullable until
    # someone on your team claims it.
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=True)   # nullable until the business picks a slot
    status = Column(String(50), nullable=False, default=InterviewStatusEnum.pending.value)
    interview_type = Column(String(50), nullable=True)   # virtual | in_person | phone

    meeting_url = Column(String(500), nullable=True)   # e.g. a Zoom/Meet link, filled in once scheduled
    location = Column(String(500), nullable=True)      # only relevant if interview_type == in_person
    notes = Column(String(1000), nullable=True)         # business owner's "anything you'd like us to know" field
    outcome = Column(String(500), nullable=True)        # admin's notes after the call happens

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())