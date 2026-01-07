from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Account
from schemas import AccountCreate
from deps import get_db, get_current_user
from fastapi import Depends
from auth import get_current_user
from database import get_db


router = APIRouter()
@router.post("/")
def create_account(data: AccountCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    acc = Account(**data.dict(), user_id=user.id)
    db.add(acc)
    db.commit()
    return acc

@router.post("/", summary="Create Account")
def create_account(
    account: AccountCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)):
    new_account = Account(
        bank_name=account.bank_name,
        account_type=account.account_type,
        balance=account.balance,
        user_id=current_user.id
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)   # 🔥 important

    return new_account

@router.get("/", summary="Get Account")
def get_accounts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Account).filter(Account.user_id == user.id).all()

@router.delete("/{account_id}", summary="Delete Account")
def delete_account(account_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    acc = db.query(Account).filter(Account.id == account_id).first()
    db.delete(acc)
    db.commit()
    return {"message": "Deleted"}


    