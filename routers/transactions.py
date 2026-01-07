import csv
from io import StringIO
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models import Transaction, Account
from schemas import TransactionCreate
from deps import get_db, get_current_user

router = APIRouter()

@router.post("/", summary="Create Account")
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    account = db.query(Account).filter(
        Account.id == data.account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    transaction = Transaction(
        account_id=data.account_id,
        amount=data.amount,
        type=data.type
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction

@router.post("/upload-csv",summary="upload-csv")
def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))
    for row in reader:
        acc = db.query(Account).filter(Account.id == int(row["account_id"])).first()
        amount = float(row["amount"])
        acc.balance += amount if row["type"] == "credit" else -amount
        db.add(Transaction(**row))
    db.commit()
    return {"message": "CSV uploaded"}