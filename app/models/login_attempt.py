from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class LoginStatusEnum(str, enum.Enum):
    success = "success"
    failed = "failed"


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    device_info = Column(String(255), nullable=True)
    status = Column(Enum(LoginStatusEnum), nullable=False)
    failure_reason = Column(String(255), nullable=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())