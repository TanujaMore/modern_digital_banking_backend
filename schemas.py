from pydantic import BaseModel,EmailStr,Field
from typing import Optional
from datetime import datetime

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




