from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class RoleEnum(str, enum.Enum):
    client = "client"
    business_owner = "business_owner"
    admin = "admin"


class StatusEnum(str, enum.Enum):
    active = "active"
    pending = "pending"
    suspended = "suspended"


class AuthProviderEnum(str, enum.Enum):
    google = "google"
    both = "both"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    google_id = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    profile_photo = Column(String(500), nullable=True)
    role = Column(Enum(RoleEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.active)
    is_email_verified = Column(Boolean, default=True)
    has_set_password = Column(Boolean, default=False)
    auth_provider = Column(Enum(AuthProviderEnum), default=AuthProviderEnum.google)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())