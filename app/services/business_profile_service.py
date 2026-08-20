# app/services/business_profile_service.py
#
# Same "service layer" pattern as project_service.py — the endpoint stays
# thin, the actual logic (create, fetch, ownership checks) lives here.

from sqlalchemy.orm import Session as DBSession
from app.models.business_profile import BusinessProfile


def create_or_update_business_profile(db: DBSession, user_id, data: dict) -> BusinessProfile:
    """
    Step 1 of the wizard calls this. If the logged-in user already has a
    business profile, we UPDATE it instead of creating a second one —
    that's what stops someone accidentally ending up with two businesses
    just by resubmitting the form.
    """
    existing = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()

    if existing:
        # Update every field that was actually sent — this lets someone
        # come back and edit their profile later, not just create it once.
        for key, value in data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    # No existing profile — create a brand new one.
    profile = BusinessProfile(user_id=user_id, **data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_my_business_profile(db: DBSession, user_id) -> BusinessProfile:
    """
    Fetches the logged-in business owner's own profile.
    Used to pre-fill Step 1 if they're coming back to edit it.
    """
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()
    if not profile:
        raise ValueError("No business profile found for this account yet")
    return profile