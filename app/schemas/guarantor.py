# app/schemas/guarantor.py

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.guarantor import ContactTypeEnum


class GuarantorRequest(BaseModel):
    contact_type: str   # "guarantor" or "next_of_kin"
    full_name: str
    relationship: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    employer: Optional[str] = None
    job_title: Optional[str] = None

    @field_validator("contact_type")
    @classmethod
    def validate_contact_type(cls, value: str) -> str:
        valid = [t.value for t in ContactTypeEnum]
        if value not in valid:
            raise ValueError(f"contact_type must be one of: {', '.join(valid)}")
        return value


class GuarantorResponse(BaseModel):
    id: str
    user_id: str
    contact_type: str
    full_name: str
    relationship: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    employer: Optional[str] = None
    job_title: Optional[str] = None
    created_at: datetime

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True