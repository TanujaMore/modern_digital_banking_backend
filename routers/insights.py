from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import get_db
from models import Transaction, Account
from auth import get_current_user

router = APIRouter(prefix="/insights", tags=["Insights"])


# ===============================
# Monthly Cashflow
# ===============================
@router.get("/monthly-cashflow")
def monthly_cashflow(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    results = (
        db.query(
            func.date_trunc("month", Transaction.txn_date).label("month"),
            Transaction.txn_type,
            func.sum(Transaction.amount).label("total")
        )
        .join(Account, Account.id == Transaction.account_id)
        .filter(Account.user_id == current_user.id)
        .group_by("month", Transaction.txn_type)
        .order_by("month")
        .all()
    )

    data = {}
    for row in results:
        month = row.month.strftime("%Y-%m")
        data.setdefault(month, {"income": 0, "expense": 0})

        if row.txn_type == "credit":
            data[month]["income"] += float(row.total)
        else:
            data[month]["expense"] += float(row.total)

    return data


# ===============================
# Spending by Category
# ===============================
@router.get("/spending-by-category")
def spending_by_category(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    results = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total")
        )
        .join(Account, Account.id == Transaction.account_id)
        .filter(
            Account.user_id == current_user.id,
            Transaction.txn_type == "debit"
        )
        .group_by(Transaction.category)
        .all()
    )

    return [
        {"category": r.category or "Other", "amount": float(r.total)}
        for r in results
    ]


# ===============================
# Top Merchants
# ===============================
@router.get("/top-merchants")
def top_merchants(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    results = (
        db.query(
            Transaction.merchant,
            func.sum(Transaction.amount).label("total")
        )
        .join(Account, Account.id == Transaction.account_id)
        .filter(
            Account.user_id == current_user.id,
            Transaction.txn_type == "debit"
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )

    return [
        {"merchant": r.merchant or "Unknown", "amount": float(r.total)}
        for r in results
    ]


# ===============================
# Burn Rate (Last 30 Days)
# ===============================
@router.get("/burn-rate")
def burn_rate(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    start_date = datetime.utcnow() - timedelta(days=30)

    total_spent = (
        db.query(func.sum(Transaction.amount))
        .join(Account, Account.id == Transaction.account_id)
        .filter(
            Account.user_id == current_user.id,
            Transaction.txn_type == "debit",
            Transaction.txn_date >= start_date
        )
        .scalar()
        or 0
    )

    return {
        "burn_rate": round(float(total_spent) / 30, 2)
    }
