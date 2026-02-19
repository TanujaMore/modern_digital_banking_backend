from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
import csv, io
from datetime import datetime
from decimal import Decimal

from routers.categorize import auto_assign_category
from database import get_db
from auth import get_current_user
from models import User, Account, Transaction, Category, Reward
from schemas import TransactionCreate, TransactionResponse
from utils.alert_helper import create_alert

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.get("/")
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == current_user.id)
        .order_by(Transaction.txn_date.desc())
        .all()
    )

# =====================================================
# GET ALL TRANSACTIONS
# =====================================================

# =====================================================
# GET ALL CATEGORIES
# =====================================================
@router.get("/categories")
def get_all_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Category).all()

# =====================================================
# GET TRANSACTIONS FOR ACCOUNT
# =====================================================
@router.get("/{account_id}", response_model=List[TransactionResponse])
def get_transactions(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).all()

# =====================================================
# CREATE TRANSACTION (FIXED)
# =====================================================
@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(Account).filter(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    txn_type = transaction.txn_type.lower()
    amount = Decimal(str(transaction.amount))

    # -------------------------------
    # UPDATE BALANCE
    # -------------------------------
    if txn_type == "credit":
        account.balance += float(amount)
    elif txn_type == "debit":
        account.balance -= float(amount)
    else:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    # -------------------------------
    # CREATE TRANSACTION
    # -------------------------------
    new_txn = Transaction(
        account_id=transaction.account_id,
        amount=amount,
        txn_type=txn_type,
        txn_date=transaction.txn_date or datetime.utcnow(),
        description=transaction.description,
        merchant=transaction.merchant,
        currency=transaction.currency or "INR"
    )

    new_txn.category = auto_assign_category(db, new_txn)
    db.add(new_txn)

    # -------------------------------
    # ALERTS (SAFE)
    # -------------------------------
    try:
        if account.balance < 1000:
            create_alert(
                db=db,
                user_id=current_user.id,
                alert_type="low_balance",
                title="Low Balance",
                message=f"Your account balance is low (₹{account.balance})",
                severity="warning"
            )

        if txn_type == "debit" and amount >= 10000:
            create_alert(
                db=db,
                user_id=current_user.id,
                alert_type="large_transaction",
                title="Large Transaction",
                message=f"₹{amount} spent at {transaction.merchant}",
                severity="warning"
            )
    except Exception:
        pass  # alerts must NEVER block transaction

    # -------------------------------
    # REWARDS
    # -------------------------------
    if txn_type == "debit":
        points = int(amount // 100)

        if points > 0:
            reward = db.query(Reward).filter(
                Reward.user_id == current_user.id,
                Reward.program_name == "Bank Rewards"
            ).first()

            if not reward:
                reward = Reward(
                    user_id=current_user.id,
                    program_name="Bank Rewards",
                    points_balance=0
                )
                db.add(reward)

            reward.points_balance += points

    db.commit()
    db.refresh(new_txn)
    return new_txn

# =====================================================
# CSV UPLOAD (FIXED)
# =====================================================
@router.post("/upload-csv")
def upload_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contents = file.file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(contents)

    for row in reader:
        # ---- account_id (safe) ----
        account_id = row.get("account_id")

        if not account_id:
            account = db.query(Account).filter(
                Account.user_id == current_user.id
            ).first()
            if not account:
                raise HTTPException(status_code=400, detail="No account found")
        else:
            account = db.query(Account).filter(
                Account.id == int(account_id),
                Account.user_id == current_user.id
            ).first()
            if not account:
                raise HTTPException(status_code=403, detail="Invalid account_id")

        # ---- amount ----
        amount = row.get("amount")
        if not amount:
            raise HTTPException(status_code=400, detail="CSV missing amount")

        # ---- txn_date ----
        txn_date = (
            datetime.fromisoformat(row["txn_date"])
            if row.get("txn_date")
            else datetime.utcnow()
        )

        txn = Transaction(
            account_id=account.id,
            description=row.get("description"),
            merchant=row.get("merchant"),
            amount=float(amount),
            txn_type=row.get("txn_type", "").lower(),
            currency=row.get("currency", "INR"),
            category=row.get("category", "Others"),
            txn_date=txn_date,
        )

        db.add(txn)

    db.commit()
    return {"message": "CSV uploaded successfully"}



# =====================================================
# UPDATE CATEGORY
# =====================================================
@router.put("/{txn_id}/category")
def update_transaction_category(
    txn_id: int,
    category: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()

    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn.category = category
    db.commit()
    return {"message": "Category updated"}
