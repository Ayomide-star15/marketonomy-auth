# app/api/v1/endpoints/projects.py
#
# This is the "API layer" — the part that actually turns URLs + HTTP
# methods into working endpoints. Same pattern as your existing
# app/api/v1/endpoints/auth.py.
#
# Notice how SHORT each function is — that's deliberate. All the real
# logic lives in project_service.py. Each endpoint here just does three
# things: (1) accept the request, (2) call the service function,
# (3) turn any error into the right HTTP status code.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List

from app.db.database import get_db
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    MilestoneCreateRequest,
    MilestoneResponse,
)
from app.services.project_service import (
    create_project,
    get_client_projects,
    add_milestone,
)
from app.core.dependencies import get_current_user   # the same JWT-checking dependency your auth endpoints use
from app.models.user import User

# prefix="/projects" means every route below actually lives at
# /api/v1/projects/... once this router is registered in main.py.
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectResponse])
def list_my_projects(
    current_user: User = Depends(get_current_user),   # FastAPI runs this first — decodes the JWT,
                                                        # rejects the request with 401 if the token is bad,
                                                        # and hands us back the actual logged-in User row.
    db: DBSession = Depends(get_db),                   # a fresh database session for this one request
):
    """
    Returns everything the CURRENTLY LOGGED-IN client has commissioned.
    This is the first endpoint to test — if this works, it proves your
    auth + database + ORM are all wired together correctly.
    """
    return get_client_projects(db, current_user.id)


@router.post("", response_model=ProjectResponse)
def start_project(
    data: ProjectCreateRequest,   # FastAPI automatically parses + validates the JSON body into this schema
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """
    Client starts a new project with a business.
    Notice we use current_user.id for client_id — never data.client_id —
    so a client can never claim to be someone else.
    """
    project = create_project(
        db,
        client_id=current_user.id,
        business_id=data.business_id,
        name=data.name,
        start_date=data.start_date,
    )
    return project


@router.post("/{project_id}/milestones", response_model=MilestoneResponse)
def create_milestone(
    project_id: str,               # comes from the URL itself, e.g. /projects/abc123/milestones
    data: MilestoneCreateRequest,  # comes from the request body
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """
    Add a payment milestone to an existing project.
    """
    try:
        milestone = add_milestone(
            db,
            project_id=project_id,
            client_id=current_user.id,
            name=data.name,
            amount=data.amount,
            due_date=data.due_date,
        )
        return milestone
    except ValueError as e:
        # The service layer raises plain ValueErrors (e.g. "Project not
        # found"). We catch them here and turn them into a proper HTTP
        # error response — this is the same pattern your existing
        # auth.py endpoints use.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))