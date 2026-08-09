# app/models/project.py
#
# This file defines two DATABASE TABLES as Python classes, using SQLAlchemy

from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base  # the shared base class every model must inherit from


class Project(Base):
    """
    Represents one row in the 'projects' table.
    A Project = "this client hired this business to do this piece of work."
    """

    __tablename__ = "projects"  # must match the exact table name in Supabase

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=False)

    # Plain text field, e.g. "Mobile App MVP". Required.
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending | in_progress | completed

    # Optional — a project might not have a confirmed start date yet.
    start_date = Column(Date, nullable=True)

    # Automatically set by Postgres itself the moment the row is created.
    # You never set this in your Python code.
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectMilestone(Base):
    """
    Represents one row in the 'project_milestones' table.
    A milestone = one payment checkpoint inside a project.
    One Project can have MANY milestones (e.g. "Deposit", "Beta build", "Launch").
    """

    __tablename__ = "project_milestones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # e.g. "Milestone 1 — Design sign-off"
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    # Same free-text status pattern as Project.status above.
    status = Column(String(50), nullable=False, default="upcoming")  # upcoming | due | paid

    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())