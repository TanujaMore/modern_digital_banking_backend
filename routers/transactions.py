from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
import csv, io
from datetime import datetime
from sqlalchemy import func

from routers.categorize import auto_assign_category
from database import get_db
from auth import get_current_user
from models import User, Account, Transaction, Category, Reward
from schemas import TransactionCreate, TransactionResponse

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

# =====================================================
# GET ALL TRANSACTIONS (LOGGED IN USER)
# =====================================================
@router.get("/", response_model=List[TransactionResponse])
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Transaction)
        .join(Account)
        .filter(Account.user_id == current_user.id)
        .all()
    )

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
# CATEGORY SUMMARY (FOR CHARTS / BUDGETS)
# =====================================================
@router.get("/category-summary")
def get_category_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = (
        db.query(Transaction.category, func.sum(Transaction.amount).label("total"))
        .join(Account)
        .filter(
            Account.user_id == current_user.id,
            Transaction.txn_type == "debit"
        )
        .group_by(Transaction.category)
        .all()
    )

    return [
        {"category": row[0], "total": float(row[1])}
        for row in result
    ]

# =====================================================
# GET TRANSACTIONS FOR SPECIFIC ACCOUNT
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
# CREATE NEW TRANSACTION (AUTO REWARD SYSTEM – FIXED)
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

    # -------------------------------
    # UPDATE ACCOUNT BALANCE
    # -------------------------------
    if transaction.txn_type.lower() == "credit":
        account.balance += transaction.amount
    elif transaction.txn_type.lower() == "debit":
        account.balance -= transaction.amount
    else:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    # -------------------------------
    # CREATE TRANSACTION
    # -------------------------------
    new_txn = Transaction(
        account_id=transaction.account_id,
        amount=transaction.amount,
        txn_type=transaction.txn_type,
        txn_date=transaction.txn_date or datetime.utcnow(),
        description=transaction.description,
        merchant=transaction.merchant,
        currency=transaction.currency
    )

    new_txn.category = auto_assign_category(db, new_txn)
    db.add(new_txn)

    # =================================================
    # 🔥 AUTO REWARD SYSTEM (₹100 = 1 POINT)
    # =================================================
    if transaction.txn_type.lower() == "debit":
        earned_points = int(transaction.amount // 100)

        if earned_points > 0:
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

            reward.points_balance += earned_points

    db.commit()
    db.refresh(new_txn)
    return new_txn

# =====================================================
# CSV UPLOAD (NOW WITH REWARD SUPPORT)
# =====================================================
@router.post("/upload-csv")
def upload_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    created = 0

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

    for row in reader:
        if "account_id" not in row:
            continue

        account = db.query(Account).filter(
            Account.id == int(row["account_id"]),
            Account.user_id == current_user.id
        ).first()

        if not account:
            continue

        amount = float(row["amount"])
        txn_type = row["txn_type"].lower()

        if txn_type == "credit":
            account.balance += amount
        elif txn_type == "debit":
            account.balance -= amount
        else:
            continue

        txn = Transaction(
            account_id=account.id,
            amount=amount,
            txn_type=txn_type,
            description=row.get("description"),
            merchant=row.get("merchant"),
            txn_date=datetime.utcnow()
        )

        txn.category = auto_assign_category(db, txn)
        db.add(txn)
        created += 1

        # 🔥 Reward for CSV debit
        if txn_type == "debit":
            reward.points_balance += int(amount // 100)

    db.commit()
    return {"message": f"{created} transactions uploaded successfully"}

# =====================================================
# UPDATE CATEGORY (MANUAL)
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
    db.refresh(txn)

    return {
        "message": "Category updated successfully",
        "transaction_id": txn.id,
        "new_category": txn.category
    }
