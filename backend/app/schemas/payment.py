from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    charging_session_id: int
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: str = "INR"
    payment_method: str = "simulated_card"


class PaymentResponse(BaseModel):
    id: int
    charging_session_id: int
    amount: float
    currency: str
    payment_method: str
    status: str
    transaction_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
