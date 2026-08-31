# app/schemas/business_bank_details.py
#
# Bank Details + NIN — typed fields the business owner submits directly,
# no file involved for bank details. NIN's matching photo is uploaded
# separately via the documents endpoint (document_type='nin_document').

from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID


class BusinessBankDetailsRequest(BaseModel):
    bank_name: str
    account_name: str
    account_number: str
    nin_number: str

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, value: str) -> str:
        if not value.strip().isdigit():
            raise ValueError("Account number must contain only digits")
        return value.strip()

    @field_validator("nin_number")
    @classmethod
    def validate_nin_number(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.isdigit() or len(cleaned) != 11:
            raise ValueError("NIN must be exactly 11 digits")
        return cleaned


class BusinessBankDetailsResponse(BaseModel):
    id: str
    business_profile_id: str
    bank_name: str
    account_name: str
    account_number: str
    nin_number: str
    is_verified: bool
    created_at: datetime

    @field_validator("id", "business_profile_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True