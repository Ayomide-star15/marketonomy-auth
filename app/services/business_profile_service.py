# app/services/business_profile_service.py
#
# Same "service layer" pattern as project_service.py — the endpoint stays
# thin, the actual logic (create, fetch, ownership checks) lives here.

from sqlalchemy.orm import Session as DBSession
from app.models.business_profile import BusinessProfile, BusinessProfileStatusEnum


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

    profile.status = BusinessProfileStatusEnum.pending_review.value
    profile.rejection_reason = None  # clear any stale rejection reason from a prior cycle
    db.commit()
    db.refresh(profile)
    return profile


def approve_business_profile(db: DBSession, business_id: str) -> BusinessProfile:
    """
    Admin-only action. Flips pending_review -> approved.
    This is the exact moment a business becomes visible on Market.
    """
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == business_id).first()
    if not profile:
        raise ValueError("Business profile not found")

    if profile.status != BusinessProfileStatusEnum.pending_review.value:
        raise ValueError(f"Cannot approve — profile is currently '{profile.status}', not 'pending_review'")

    profile.status = BusinessProfileStatusEnum.approved.value
    profile.rejection_reason = None
    db.commit()
    db.refresh(profile)
    return profile


def reject_business_profile(db: DBSession, business_id: str, reason: str) -> BusinessProfile:
    """
    Admin-only action. Flips pending_review -> rejected, with a reason
    the business owner can see (per PRD 1.3: "Approve or reject a
    business, with a reason if rejected").
    """
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == business_id).first()
    if not profile:
        raise ValueError("Business profile not found")

    if profile.status != BusinessProfileStatusEnum.pending_review.value:
        raise ValueError(f"Cannot reject — profile is currently '{profile.status}', not 'pending_review'")

    if not reason or not reason.strip():
        raise ValueError("A reason is required when rejecting a business profile")

    profile.status = BusinessProfileStatusEnum.rejected.value
    profile.rejection_reason = reason
    db.commit()
    db.refresh(profile)
    return profile