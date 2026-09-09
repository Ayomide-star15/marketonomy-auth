# app/services/business_profile_service.py
#
# Same "service layer" pattern as project_service.py — the endpoint stays
# thin, the actual logic (create, fetch, ownership checks) lives here.

from sqlalchemy.orm import Session as DBSession
from app.models.business_profile import (
    BusinessProfile, 
    BusinessProfileStatusEnum,
)

from app.services.business_document_service import has_required_documents
from app.services.guarantor_service import has_required_contacts


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

def submit_for_review(db: DBSession, user_id) -> BusinessProfile:
    """
    Business owner clicks "Publish My Profile" (Step 5/6 of the wizard).
    Flips draft -> pending_review.

    NOTE: this intentionally does NOT yet check that required documents
    exist (business_documents isn't built yet — that's BE-002/BE-004 from
    the task board). Once that's built, add a check here before allowing
    the transition, per the PRD's "nothing to check before submit" gap.
    """
    profile = get_my_business_profile(db, user_id)

    if profile.status != BusinessProfileStatusEnum.draft.value:
        raise ValueError(f"Cannot submit for review — profile is already '{profile.status}'")
    
    if not has_required_documents(db, profile.id):
        raise ValueError(f"Please submit all 5 required documents before submitting for review")

    if not has_required_contacts(db, user_id):
        raise ValueError("Please add a guarantor before submitting for review")

    profile.status = BusinessProfileStatusEnum.pending_review.value
    profile.rejection_reason = None  # clear any stale rejection reason from a prior cycle
    db.commit()
    db.refresh(profile)
    return profile

def get_business_profile_by_id(db: DBSession, business_id) -> BusinessProfile:
    """
    Fetches any business profile by its ID.
    Only returns the profile if it has been approved by an admin.
    Used by clients browsing the market to view a business's public profile.
    """
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == business_id).first()
    if not profile:
        raise ValueError("Business profile not found")
    if profile.status != BusinessProfileStatusEnum.approved.value:
        raise ValueError("This business profile is not publicly available")
    return profile