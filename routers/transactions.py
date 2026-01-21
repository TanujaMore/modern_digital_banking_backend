from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv, io

from database import get_db
from auth import get_current_user
from models import User, Account, Transaction
from schemas import TransactionCreate, TransactionResponse

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

# 🔹 GET ALL TRANSACTIONS FOR AN ACCOUNT
@router.get("/{account_id}", response_model=List[TransactionResponse])
def get_transactions(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check account belongs to user
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).all()


# 🔹 CREATE NEW TRANSACTION (CREDIT / DEBIT)
@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check account belongs to user
    account = db.query(Account).filter(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # 🔥 UPDATE ACCOUNT BALANCE
    if transaction.txn_type.lower() == "credit":
        account.balance += transaction.amount
    elif transaction.txn_type.lower() == "debit":
        account.balance -= transaction.amount
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid transaction type (use 'credit' or 'debit')"
        )

    # 🔹 CREATE TRANSACTION RECORD
    new_txn = Transaction(
        account_id=transaction.account_id,
        amount=transaction.amount,
        txn_type=transaction.txn_type,
        description=transaction.description
    )

    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)

    return new_txn


# 🔹 UPLOAD TRANSACTIONS FROM CSV
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

        # Check account belongs to user
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user.id
        ).first()

        if not account:
            continue

        amount = float(row["amount"])
        txn_type = row["txn_type"].lower()

        # 🔥 UPDATE BALANCE
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
            description=row.get("description")
        )

        db.add(txn)
        created += 1

    db.commit()
    return {"message": f"{created} transactions uploaded successfully"}
