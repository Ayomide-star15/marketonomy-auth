# app/models/payment.py
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which milestone this payment is for.
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("project_milestones.id"), nullable=False)

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Who paid, and who got paid — useful for querying "all payments this
    # client has ever made" or "all payments this business has received"
    # without joining through project/milestone every time.
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)

    # Defaults to USD but stored as a column (not hardcoded) so a future
    # business in another country isn't a painful schema migration later.
    currency = Column(String(10), nullable=False, default="USD")

    # The four states a payment can be in, agreed with the other dev.
    status = Column(String(50), nullable=False, default="outstanding")  # outstanding | paid | failed | refunded

    payment_method = Column(String(50), nullable=True)   # e.g. "card", "bank_transfer" — filled in once paid

    # These two are for when we plug in a REAL payment processor
    # (Stripe, Paystack, etc). They stay NULL/empty until that happens —
    # having the columns now means we don't need a migration later.
    processor = Column(String(50), nullable=True)             # e.g. "stripe"
    processor_reference = Column(String(255), nullable=True)  # the processor's own transaction ID,
                                                                # used to look up a charge if a client disputes it

    invoice_date = Column(Date, nullable=True)          # when the milestone was invoiced (flipped to "due")
    paid_at = Column(DateTime(timezone=True), nullable=True)   # when it actually got paid successfully
    failure_reason = Column(String(255), nullable=True)        # why it failed, if status == "failed"

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # onupdate=func.now() means Postgres automatically bumps this timestamp
    # every time any column on this row changes — you don't set it manually.
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())