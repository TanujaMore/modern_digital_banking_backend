from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, Account
from database import get_db
from auth import get_current_user
from schemas import AccountCreate, AccountResponse



router = APIRouter(tags=["Accounts"])


@router.get("/", response_model=list[AccountResponse])
def get_accounts(
    db: Session = Depends(get_db),
    current_user:User = Depends(get_current_user)
):
    return db.query(Account).filter(
        Account.user_id == current_user.id
    ).all()


@router.post("/",)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise
    HTTPException(status_code=401,detail="User not authenticated")

    new_account = Account(
        bank_name=account.bank_name,
        account_type=account.account_type,
        balance=account.balance,
        user_id=current_user.id
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

@router.delete("/{account_id}")
def delete_account(
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

    db.delete(account)
    db.commit()
    return {"message": "Account deleted"}