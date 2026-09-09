# app/services/guarantor_service.py
#
# Unlike business_documents/business_bank_details, this is keyed to
# user_id directly (matches the live table). A business owner can have
# AT MOST one 'guarantor' row and one 'next_of_kin' row — enforced here
# in the service layer since there's no unique DB constraint on
# (user_id, contact_type) to lean on.

from sqlalchemy.orm import Session as DBSession
from app.models.guarantor import Guarantor, ContactTypeEnum


def create_or_update_contact(db: DBSession, user_id, data: dict) -> Guarantor:
    """
    Upsert, same pattern as everywhere else — one row per (user_id,
    contact_type) pair. Submitting again for the same contact_type
    updates the existing row instead of creating a duplicate.
    """
    contact_type = data["contact_type"]

    existing = (
        db.query(Guarantor)
        .filter(Guarantor.user_id == user_id)
        .filter(Guarantor.contact_type == contact_type)
        .first()
    )

    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    contact = Guarantor(user_id=user_id, **data)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_my_contacts(db: DBSession, user_id) -> list[Guarantor]:
    """Both the guarantor and next-of-kin rows for this business owner, if they exist."""
    return db.query(Guarantor).filter(Guarantor.user_id == user_id).all()


def has_required_contacts(db: DBSession, user_id) -> bool:
    """
    Used by the final submit-for-review gate — both a guarantor AND a
    next-of-kin must be on file before submission, per the wizard.
    """
    contacts = get_my_contacts(db, user_id)
    types_present = {c.contact_type for c in contacts}
    return {ContactTypeEnum.guarantor.value, ContactTypeEnum.next_of_kin.value}.issubset(types_present)