# app/schemas/payment.py
# Same idea as project.py — these define the JSON shape for the API,
# separate from the database table shape in app/models/payment.py.

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# ===== PAY A MILESTONE =====
# What the frontend sends when the client clicks "Pay Now".
# Right now this is intentionally minimal (just which payment method).
# Once a real processor (Stripe/Paystack) is wired in, this is where
# you'd add fields like a card token — the frontend never sends raw
# card numbers to your backend, it sends a token from the processor's
# own secure widget instead.
class PayMilestoneRequest(BaseModel):
    payment_method: str = "card"


# ===== PAYMENT RESPONSE =====
# What one row of "Payment History" looks like when sent to the frontend.
class PaymentResponse(BaseModel):
    id: str
    milestone_id: str
    project_id: str
    amount: Decimal
    currency: str
    status: str                          # outstanding | paid | failed | refunded
    payment_method: Optional[str] = None
    invoice_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== PAYMENTS SUMMARY =====
# Powers the two stat cards at the top of the Payments page:
# "Total Amount Paid" and "Outstanding Balance".
# This is a small, separate schema because it's not one database row —
# it's a CALCULATED result (a sum), built by the service layer.
class PaymentsSummaryResponse(BaseModel):
    total_paid: Decimal
    outstanding_balance: Decimal