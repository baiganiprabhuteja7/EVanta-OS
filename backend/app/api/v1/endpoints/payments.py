from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.charging_session import ChargingSession
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


def _payment_to_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        charging_session_id=payment.charging_session_id,
        amount=float(payment.amount),
        currency=payment.currency,
        payment_method=payment.payment_method,
        status=payment.status,
        transaction_reference=payment.transaction_reference,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve simulated payment records."""
    payments = db.scalars(
        select(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(limit)
    ).all()
    return [_payment_to_response(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific payment transaction."""
    payment = db.scalar(select(Payment).where(Payment.id == payment_id))
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment record with ID {payment_id} not found.",
        )
    return _payment_to_response(payment)


@router.post("/simulate", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def simulate_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
):
    """
    Simulate a payment transaction for a charging session.
    (Clearly identified simulated payment flow).
    """
    session = db.scalar(
        select(ChargingSession).where(ChargingSession.id == payment_in.charging_session_id)
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging session ID {payment_in.charging_session_id} not found.",
        )

    amount = payment_in.amount or session.total_amount
    payment = Payment(
        charging_session_id=session.id,
        amount=amount,
        currency=payment_in.currency or "INR",
        payment_method=payment_in.payment_method or "simulated_card",
        status="completed",
        transaction_reference=f"TXN-SIM-{uuid.uuid4().hex[:12].upper()}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return _payment_to_response(payment)
