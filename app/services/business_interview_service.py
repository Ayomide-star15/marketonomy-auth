# app/services/business_interview_service.py

from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone

from app.models.business_interview import BusinessInterview, InterviewStatusEnum
from app.models.business_profile import BusinessProfile


def get_business_profile_for_user(db: DBSession, user_id) -> BusinessProfile:
    profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()
    if not profile:
        raise ValueError("You must create a business profile before booking an interview")
    return profile


def book_interview(db: DBSession, user_id, scheduled_at, interview_type: str, location=None, notes=None) -> BusinessInterview:
    """
    Business owner books their onboarding call — Step 6 of the wizard.
    Only one ACTIVE (pending/scheduled) interview allowed at a time —
    if they already have one, this updates it instead of creating a
    second competing booking.
    """
    profile = get_business_profile_for_user(db, user_id)

    if scheduled_at <= datetime.now(timezone.utc):
        raise ValueError("Interview time must be in the future")

    existing_active = (
        db.query(BusinessInterview)
        .filter(BusinessInterview.business_profile_id == profile.id)
        .filter(BusinessInterview.status.in_([InterviewStatusEnum.pending.value, InterviewStatusEnum.scheduled.value]))
        .first()
    )

    if existing_active:
        existing_active.scheduled_at = scheduled_at
        existing_active.interview_type = interview_type
        existing_active.location = location
        existing_active.notes = notes
        existing_active.status = InterviewStatusEnum.scheduled.value
        db.commit()
        db.refresh(existing_active)
        return existing_active

    interview = BusinessInterview(
        business_profile_id=profile.id,
        scheduled_at=scheduled_at,
        interview_type=interview_type,
        location=location,
        notes=notes,
        status=InterviewStatusEnum.scheduled.value,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def get_my_interview(db: DBSession, user_id) -> BusinessInterview:
    profile = get_business_profile_for_user(db, user_id)
    interview = (
        db.query(BusinessInterview)
        .filter(BusinessInterview.business_profile_id == profile.id)
        .order_by(BusinessInterview.created_at.desc())
        .first()
    )
    if not interview:
        raise ValueError("No interview booked yet")
    return interview


def cancel_interview(db: DBSession, user_id, interview_id: str) -> BusinessInterview:
    profile = get_business_profile_for_user(db, user_id)

    interview = (
        db.query(BusinessInterview)
        .filter(BusinessInterview.id == interview_id)
        .filter(BusinessInterview.business_profile_id == profile.id)
        .first()
    )
    if not interview:
        raise ValueError("Interview not found")

    interview.status = InterviewStatusEnum.cancelled.value
    db.commit()
    db.refresh(interview)
    return interview


def has_completed_or_scheduled_interview(db: DBSession, business_profile_id) -> bool:
    """
    Used by submit_for_review gate — a business must at least have
    BOOKED an interview (scheduled or already completed) before
    submitting. Doesn't require it to have already happened — per your
    PRD, admin approval "may include that interview taking place",
    meaning review can start once it's booked, not necessarily finished.
    """
    interview = (
        db.query(BusinessInterview)
        .filter(BusinessInterview.business_profile_id == business_profile_id)
        .filter(BusinessInterview.status.in_([InterviewStatusEnum.scheduled.value, InterviewStatusEnum.completed.value]))
        .first()
    )
    return interview is not None