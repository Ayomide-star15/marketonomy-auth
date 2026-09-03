# app/services/business_bank_details_service.py
#
# Same upsert pattern as business_profile_service.py — a business
# submits Bank Details + NIN once, can come back and edit it later.

from sqlalchemy.orm import Session as DBSession

from app.models.business_bank_details import BusinessBankDetails
from app.models.business_profile import BusinessProfile


def get_business_profile_for_user(db: DBSession, user_id) -> BusinessProfile:
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()
    if not profile:
        raise ValueError("You must create a business profile before submitting bank details")
    return profile


def create_or_update_bank_details(db: DBSession, user_id, data: dict) -> BusinessBankDetails:
    profile = get_business_profile_for_user(db, user_id)

    existing = (
        db.query(BusinessBankDetails)
        .filter(BusinessBankDetails.business_profile_id == profile.id)
        .first()
    )

    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    bank_details = BusinessBankDetails(business_profile_id=profile.id, **data)
    db.add(bank_details)
    db.commit()
    db.refresh(bank_details)
    return bank_details


def get_my_bank_details(db: DBSession, user_id) -> BusinessBankDetails:
    profile = get_business_profile_for_user(db, user_id)
    record = (
        db.query(BusinessBankDetails)
        .filter(BusinessBankDetails.business_profile_id == profile.id)
        .first()
    )
    if not record:
        raise ValueError("No bank details submitted yet")
    return record