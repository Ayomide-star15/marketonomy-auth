# app/schemas/project.py
#
# These are PYDANTIC schemas, not database models. This is a really
# important distinction:
#
#   app/models/project.py   -> defines what the DATABASE TABLE looks like
#   app/schemas/project.py  -> defines what the JSON going in/out of your
#                              API endpoints looks like
#
# They often have similar fields, but they're not the same thing. For
# example: the database stores amount as a raw number, but a "Request"
# schema only needs the fields the CLIENT is allowed to send you — it
# should never include things like `id` or `created_at`, because the
# client doesn't get to choose those, the server decides them.

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ===== CREATE PROJECT =====
# This is what the FRONTEND sends you in the request body when a client
# starts a new project. Notice it does NOT include client_id — that comes
# from the logged-in user's JWT token instead, never trust the frontend
# to tell you who it is.
class ProjectCreateRequest(BaseModel):
    business_id: str          # which business they're hiring
    name: str                 # e.g. "Mobile App MVP"
    start_date: Optional[date] = None   # optional — they might not know yet


# ===== ADD MILESTONE =====
# What the frontend sends when adding a payment milestone to a project.
class MilestoneCreateRequest(BaseModel):
    name: str
    amount: Decimal            # Decimal, not float — matches the Numeric column, avoids rounding bugs
    due_date: Optional[date] = None


# This is what you SEND BACK to the frontend after a milestone exists.
# It has more fields than the create request, because now the server
# has generated an id, a status, and a created_at timestamp.
class MilestoneResponse(BaseModel):
    id: str
    project_id: str
    name: str
    amount: Decimal
    status: str
    due_date: Optional[date] = None
    created_at: datetime

    class Config:
        # This tells Pydantic: "it's fine to build this schema directly
        # from a SQLAlchemy model object" (e.g. straight from a
        # ProjectMilestone instance), instead of requiring a plain dict.
        from_attributes = True


# ===== PROJECT RESPONSE (with milestones nested inside) =====
# What you send back when the frontend asks "give me my projects".
# Notice `milestones: List[MilestoneResponse]` — this means one Project
# response can carry its whole list of milestones inside it, so the
# frontend gets everything it needs in a single API call instead of
# having to make a second request per project.
class ProjectResponse(BaseModel):
    id: str
    client_id: str
    business_id: str
    name: str
    status: str
    start_date: Optional[date] = None
    created_at: datetime
    milestones: List[MilestoneResponse] = []   # defaults to an empty list if there are none yet

    class Config:
        from_attributes = True