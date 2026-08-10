# app/services/project_service.py
#
# This is the SERVICE LAYER — same pattern as your existing
# app/services/auth_service.py. This is where the actual business logic
# lives: creating rows, checking permissions, enforcing rules.
#
# The endpoints file (api/v1/endpoints/projects.py) stays "thin" — it just
# receives the HTTP request and calls a function from here. That split
# makes it possible to test this logic without spinning up a whole web
# server, and keeps the endpoint file easy to read.

from sqlalchemy.orm import Session as DBSession
from datetime import date, datetime, timezone

from app.models.project import Project, ProjectMilestone
from app.models.payment import Payment


def create_project(db: DBSession, client_id, business_id: str, name: str, start_date: date = None) -> Project:
    """
    A client commissions a new project with a business.
    Called when someone submits the 'Start a Project' form.
    """
    project = Project(
        client_id=client_id,      # comes from the logged-in user's token, NOT from the request body
        business_id=business_id,
        name=name,
        status="pending",         # every new project starts as "pending" until work begins
        start_date=start_date,
    )
    db.add(project)      # stage the new row
    db.commit()          # actually write it to Postgres
    db.refresh(project)  # pull back the final row (so we get the id, created_at that Postgres generated)
    return project


def get_client_projects(db: DBSession, client_id) -> list[Project]:
    """
    Everything a client has ever commissioned, newest first.
    Powers the 'Recent Projects' table and the full Projects page.
    """
    return (
        db.query(Project)
        .filter(Project.client_id == client_id)   # SECURITY: only ever return THIS client's own projects
        .order_by(Project.created_at.desc())      # newest first
        .all()
    )


def get_project_or_raise(db: DBSession, project_id: str, client_id) -> Project:
    """
    Small helper used before doing anything to a project — fetches it,
    but ALSO checks that it actually belongs to the logged-in client.
    This stops Client A from adding a milestone to Client B's project
    just by guessing a project_id.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .filter(Project.client_id == client_id)   # the ownership check
        .first()
    )
    if not project:
        # Either the project doesn't exist, OR it exists but belongs to
        # someone else — either way we return the same generic error,
        # so we don't accidentally reveal "this project exists but isn't
        # yours" to someone probing around.
        raise ValueError("Project not found")
    return project


def add_milestone(db: DBSession, project_id: str, client_id, name: str, amount, due_date: date = None) -> ProjectMilestone:
    """Add a new payment milestone to a project the client owns."""
    get_project_or_raise(db, project_id, client_id)   # ownership check happens first, before we touch anything

    milestone = ProjectMilestone(
        project_id=project_id,
        name=name,
        amount=amount,
        status="upcoming",   # brand new milestones start as "upcoming" — not invoiced yet
        due_date=due_date,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone


def invoice_milestone(db: DBSession, milestone_id: str) -> ProjectMilestone:
    """
    Flip a milestone from 'upcoming' to 'due', and create the matching
    outstanding Payment row so it shows up on the client's Payments page.

    This is the "Send Invoice" action from the business owner's side of
    the prototype — normally your colleague's backend would call this
    (or an endpoint that wraps it), since he owns the business-side flow.
    """
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise ValueError("Milestone not found")
    if milestone.status != "upcoming":
        # Guard against double-invoicing the same milestone by mistake.
        raise ValueError(f"Milestone is already '{milestone.status}'")

    # We need the parent project to know who the client/business actually are.
    project = db.query(Project).filter(Project.id == milestone.project_id).first()

    milestone.status = "due"

    # Creating the Payment row is what makes this milestone show up as
    # "Outstanding" on the client's Payments page.
    payment = Payment(
        milestone_id=milestone.id,
        project_id=project.id,
        client_id=project.client_id,
        business_id=project.business_id,
        amount=milestone.amount,
        status="outstanding",
        invoice_date=datetime.now(timezone.utc).date(),
    )
    db.add(payment)
    db.commit()
    db.refresh(milestone)
    return milestone