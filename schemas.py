from enum import Enum
from pydantic import BaseModel,EmailStr,Field
from typing import Optional
from datetime import datetime,date



class RegisterUser(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str = Field(...,min_length=10,max_length=15)

class LoginUser(BaseModel):
    email: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AccountCreate(BaseModel):
    bank_name: str
    account_type: str
    balance: float = 0
 
class AccountResponse(BaseModel):
    id: int
    bank_name: str
    account_type: str
    balance: float

    class Config:
        from_attributes = True 

class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    txn_type: str
    description: Optional[str] = None
    merchant: Optional[str] = None      # 🔥 MUST MATCH MODEL NAME
    currency: Optional[str] = None  
    txn_date: Optional[datetime] = None  

class TransactionResponse(BaseModel):
    id: int
    account_id: int
    amount: float
    txn_type: str
    description: str | None = None
    merchant: Optional[str] = None      # 🔥 ADD THIS
    currency: Optional[str] = "INR"     # 🔥 ADD THIS
    category: Optional[str] = None
    txn_date: Optional[datetime] = None 

    model_config = {
        "from_attributes": True
    }


class CategoryCreate(BaseModel):
    name: str
    keywords: str



class CategoryResponse(BaseModel):
    id: int
    name: str
    keywords: str

    class Config:
        from_attributes = True



class BudgetCreate(BaseModel):
    month: int
    year: int
    category: str
    limit_amount: float


class BudgetResponse(BudgetCreate):
    id: int
    spent_amount: float
    warning: str | None = None   # 🔥 must be here
    
    class Config:
        from_attributes = True


class BillCreate(BaseModel):
    
    biller_name: str
    amount_due: float
    due_date: date
    auto_pay: bool = False


class BillStatus(str, Enum):
    upcoming = "upcoming"
    paid = "paid"
    overdue = "overdue"

class BillUpdate(BaseModel):
    biller_name: Optional[str] = None
    amount_due: Optional[float] = None
    due_date: Optional[date] = None
    status: Optional[BillStatus] = None 

    auto_pay: Optional[bool] = None



class BillResponse(BaseModel):
    id: int
    user_id: int
    biller_name: str
    amount_due: float
    due_date: date
    status: str
    auto_pay: bool
    overdue: bool                     # 🔥 calculated, not DB column
    created_at: datetime

    class Config:
        from_attributes = True


class RewardCreate(BaseModel):
    program_name: str
    points_balance: int = 0


class RewardUpdate(BaseModel):
    points_balance: int


class RewardResponse(BaseModel):
    id: int
    program_name: str
    points_balance: int
    last_updated: datetime

    class Config:
        from_attributes = True

class RewardRedeem(BaseModel):
    reward_id: int
    account_id: int