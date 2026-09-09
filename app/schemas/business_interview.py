# app/schemas/business_interview.py

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.business_interview import InterviewTypeEnum


class BookInterviewRequest(BaseModel):
    scheduled_at: datetime
    interview_type: str
    location: Optional[str] = None   # required in practice if interview_type == "in_person"
    notes: Optional[str] = None

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, value: str) -> str:
        valid = [t.value for t in InterviewTypeEnum]
        if value not in valid:
            raise ValueError(f"interview_type must be one of: {', '.join(valid)}")
        return value


class BusinessInterviewResponse(BaseModel):
    id: str
    business_profile_id: str
    interviewer_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: str
    interview_type: Optional[str] = None
    meeting_url: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    @field_validator("id", "business_profile_id", "interviewer_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True