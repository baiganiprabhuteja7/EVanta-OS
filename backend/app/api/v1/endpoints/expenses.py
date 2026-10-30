from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, require_manager_or_admin, get_db
from app.models.station import Station
from app.models.station_expense import StationExpense
from app.models.user import User
from app.schemas.station_expense import StationExpenseCreate, StationExpenseResponse

router = APIRouter(prefix="/expenses", tags=["Station Operating Expenses"])


@router.get("", response_model=List[StationExpenseResponse])
def get_expenses(
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve recorded operating expenses for stations."""
    query = select(StationExpense).order_by(StationExpense.expense_date.desc())
    if station_id:
        query = query.where(StationExpense.station_id == station_id)

    expenses = db.scalars(query).all()
    results = []
    for exp in expenses:
        station = db.scalar(select(Station).where(Station.id == exp.station_id))
        results.append({
            "id": exp.id,
            "station_id": exp.station_id,
            "station_name": station.station_name if station else "Unknown",
            "expense_date": exp.expense_date,
            "category": exp.category,
            "amount": float(exp.amount),
            "description": exp.description,
            "recorded_by": exp.recorded_by,
            "created_at": exp.created_at,
        })
    return results


@router.post("", response_model=StationExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_in: StationExpenseCreate,
    current_operator: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Record an operational expense for a station (Station Manager or Administrator)."""
    station = db.scalar(select(Station).where(Station.id == expense_in.station_id))
    if not station:
        raise HTTPException(status_code=404, detail=f"Station with ID {expense_in.station_id} not found.")

    exp_date = expense_in.expense_date or datetime.now(timezone.utc)
    new_expense = StationExpense(
        station_id=expense_in.station_id,
        expense_date=exp_date,
        category=expense_in.category.strip(),
        amount=expense_in.amount,
        description=expense_in.description,
        recorded_by=current_operator.id,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return {
        "id": new_expense.id,
        "station_id": new_expense.station_id,
        "station_name": station.station_name,
        "expense_date": new_expense.expense_date,
        "category": new_expense.category,
        "amount": float(new_expense.amount),
        "description": new_expense.description,
        "recorded_by": new_expense.recorded_by,
        "created_at": new_expense.created_at,
    }


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete an operational expense record (Administrator only)."""
    expense = db.scalar(select(StationExpense).where(StationExpense.id == expense_id))
    if not expense:
        raise HTTPException(status_code=404, detail=f"Expense record {expense_id} not found.")

    db.delete(expense)
    db.commit()
    return {"status": "ok", "message": f"Expense record {expense_id} deleted."}
