# app/services/payment_service.py
#
# The service layer for everything Payments-related — this is where the
# real "Pay Now" logic lives.

from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone
from decimal import Decimal

from app.models.payment import Payment
from app.models.project import Project, ProjectMilestone


def get_client_payments(db: DBSession, client_id) -> list[Payment]:
    """Full payment history for the logged-in client, newest first."""
    return (
        db.query(Payment)
        .filter(Payment.client_id == client_id)
        .order_by(Payment.created_at.desc())
        .all()
    )


def get_payments_summary(db: DBSession, client_id) -> dict:
    """
    Adds up the two numbers shown at the top of the Payments page:
    'Total Amount Paid' and 'Outstanding Balance'.

    Note: for a real app with lots of payments, you'd normally do this
    sum directly in the SQL query (e.g. SUM(amount) ... GROUP BY status)
    instead of pulling every row into Python and summing it here — this
    version is simpler to read while you're still building, but worth
    revisiting once a client might have hundreds of payments.
    """
    payments = get_client_payments(db, client_id)
    total_paid = sum((p.amount for p in payments if p.status == "paid"), Decimal("0"))
    outstanding = sum((p.amount for p in payments if p.status == "outstanding"), Decimal("0"))
    return {"total_paid": total_paid, "outstanding_balance": outstanding}


def pay_milestone(db: DBSession, milestone_id: str, client_id, payment_method: str = "card") -> Payment:
    """
    The actual 'Pay Now' button's logic.

    IMPORTANT: in production, this is where you'd call out to a real
    payment processor (Stripe, Paystack, etc.) FIRST, and only mark the
    payment as 'paid' once the processor confirms the charge actually
    succeeded. Right now this function just marks it paid immediately,
    which is fine for testing the flow but is NOT how it should work
    once real money is involved — see the comment further down.
    """

    # Step 1: find the milestone being paid.
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
    if not milestone:
        raise ValueError("Milestone not found")

    # Step 2: find the OUTSTANDING payment row that was created when this
    # milestone got invoiced (see invoice_milestone() in project_service.py).
    # If there's no outstanding payment, there's nothing to pay yet.
    payment = (
        db.query(Payment)
        .filter(Payment.milestone_id == milestone_id)
        .filter(Payment.status == "outstanding")
        .first()
    )
    if not payment:
        raise ValueError("No outstanding payment found for this milestone")

    # Step 3: SECURITY CHECK — make sure the person paying is actually
    # the client this payment belongs to. Without this, Client A could
    # pay off Client B's invoice just by guessing a milestone_id.
    if payment.client_id != client_id:
        raise ValueError("You do not have permission to pay this milestone")

    # --- THIS IS WHERE A REAL PAYMENT PROCESSOR CALL GOES ---
    # Example of what it would look like with Stripe (pseudocode):
    #
    #   result = stripe.PaymentIntent.create(amount=..., currency=...)
    #   if result.status != "succeeded":
    #       payment.status = "failed"
    #       payment.failure_reason = result.error_message
    #       db.commit()
    #       raise ValueError("Payment failed: " + result.error_message)
    #
    # Right now we skip straight to marking it paid, since there's no
    # processor wired in yet.

    payment.status = "paid"
    payment.payment_method = payment_method
    payment.paid_at = datetime.now(timezone.utc)
    milestone.status = "paid"

    # Step 4: if EVERY milestone on this project is now paid, the whole
    # project automatically flips to "completed" — matches the behaviour
    # from the interactive prototype we built earlier.
    project = db.query(Project).filter(Project.id == milestone.project_id).first()
    all_milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project.id).all()
    if all(m.status == "paid" for m in all_milestones):
        project.status = "completed"

    db.commit()
    db.refresh(payment)
    return payment