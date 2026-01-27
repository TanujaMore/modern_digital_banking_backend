from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from database import get_db
from auth import get_current_user
from models import User, Account, Transaction

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# 🔹 DASHBOARD SUMMARY API
@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total accounts
    total_accounts = db.query(Account).filter(
        Account.user_id == current_user.id
    ).count()

    # Total balance (sum of all accounts)
    total_balance = db.query(func.sum(Account.balance)).filter(
        Account.user_id == current_user.id
    ).scalar() or 0

    # Current month & year
    now = datetime.now()
    month = now.month
    year = now.year

    # Monthly income
    income = (
        db.query(func.sum(Transaction.amount))
        .join(Account)
        .filter(
            Account.user_id == current_user.id,
            Transaction.txn_type == "credit",
            func.extract("month", Transaction.txn_date) == month,
            func.extract("year", Transaction.txn_date) == year,
        )
        .scalar()
        or 0
    )

    # Monthly expenses
    expenses = (
        db.query(func.sum(Transaction.amount))
        .join(Account)
        .filter(
            Account.user_id == current_user.id,
            Transaction.txn_type == "debit",
            func.extract("month", Transaction.txn_date) == month,
            func.extract("year", Transaction.txn_date) == year,
        )
        .scalar()
        or 0
    )

    return {
        "balance": float(total_balance),
        "accounts": total_accounts,
        "income": float(income),
        "expenses": float(expenses),
    }
