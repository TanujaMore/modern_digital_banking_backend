from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv, io
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel

from routers.categorize import auto_assign_category
from database import get_db
from auth import get_current_user
from models import User, Account, Transaction, Category
from schemas import TransactionCreate, TransactionResponse
from fastapi import Query



router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

# 🔹 GET ALL TRANSACTIONS (FOR LOGGED IN USER)
@router.get("/", response_model=List[TransactionResponse])
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transactions = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id
    ).all()
    return transactions


# 🔹 GET ALL CATEGORIES
@router.get("/categories")
def get_all_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).all()
    return categories


# 🔹 CATEGORY WISE SPEND SUMMARY (FOR CHARTS & BUDGETS)

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

    summary = []
    for row in result:
        summary.append({
            "category": row[0],
            "total": float(row[1])
        })

    return summary


# 🔹 GET ALL TRANSACTIONS FOR AN ACCOUNT
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


# 🔹 CREATE NEW TRANSACTION  (NOT TOUCHED)
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

    # UPDATE BALANCE
    if transaction.txn_type.lower() == "credit":
        account.balance += transaction.amount
    elif transaction.txn_type.lower() == "debit":
        account.balance -= transaction.amount
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid transaction type (use 'credit' or 'debit')"
        )

    new_txn = Transaction(
        account_id=transaction.account_id,
        amount=transaction.amount,
        txn_type=transaction.txn_type,
        txn_date=transaction.txn_date or datetime.utcnow(),
        description=transaction.description,
        merchant=transaction.merchant,
        currency=transaction.currency
    )

    # 🔥 AUTO ASSIGN CATEGORY
    category = auto_assign_category(db, new_txn)
    new_txn.category = category

    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)

    return new_txn


# 🔹 CSV UPLOAD (NOT TOUCHED)
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

    for row in reader:
        if "account_id" not in row:
            continue

        account_id = int(row["account_id"])

        account = db.query(Account).filter(
            Account.id == account_id,
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
            account_id=account_id,
            amount=amount,
            txn_type=txn_type,
            description=row.get("description"),
            merchant=row.get("merchant"),
        )

        # 🔥 AUTO ASSIGN CATEGORY
        category = auto_assign_category(db, txn)
        txn.category = category

        db.add(txn)
        created += 1

    db.commit()
    return {"message": f"{created} transactions uploaded successfully"}


# 🔹 MANUAL RECATEGORIZATION (FIXED VERSION)


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



