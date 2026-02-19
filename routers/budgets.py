from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from database import get_db
from models import Budget, Transaction, Alert
from schemas import BudgetCreate, BudgetResponse
from utils.alert_helper import create_alert
from auth import get_current_user

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)

# =================================================
# CREATE BUDGET
# =================================================
@router.post("/", response_model=BudgetResponse)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    new_budget = Budget(
        user_id=current_user.id,
        month=budget.month,
        year=budget.year,
        category=budget.category,
        limit_amount=budget.limit_amount
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


# =================================================
# LIST BUDGETS
# =================================================
@router.get("/", response_model=list[BudgetResponse])
def list_budgets(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).all()


# =================================================
# BUDGET PROGRESS + SAFE ALERT
# =================================================
@router.get("/progress", response_model=list[BudgetResponse])
def budget_progress(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).all()

    for b in budgets:
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.category == b.category,
            Transaction.txn_type == "debit",
            extract("month", Transaction.txn_date) == b.month,
            extract("year", Transaction.txn_date) == b.year
        ).scalar() or 0

        b.spent_amount = spent

        if spent > b.limit_amount:
            b.warning = "⚠️ Budget limit exceeded"

            # 🔒 CHECK IF ALERT ALREADY EXISTS
            existing_alert = db.query(Alert).filter(
                Alert.user_id == current_user.id,
                Alert.alert_type == "budget_exceeded",
                Alert.message == f"{b.category} budget exceeded for {b.month}/{b.year}"
            ).first()

            if not existing_alert:
                create_alert(
                    db=db,
                    user_id=current_user.id,
                    title="Budget Exceeded",
                    alert_type="budget_exceeded",
                    message=f"{b.category} budget exceeded for {b.month}/{b.year}",
                    severity="warning"
                )
        else:
            b.warning = "Within limit"

    db.commit()
    return budgets


# =================================================
# DELETE BUDGET
# =================================================
@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}


# =================================================
# UPDATE BUDGET
# =================================================
@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    existing = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Budget not found")

    existing.month = budget.month
    existing.year = budget.year
    existing.category = budget.category
    existing.limit_amount = budget.limit_amount

    db.commit()
    db.refresh(existing)
    return existing

