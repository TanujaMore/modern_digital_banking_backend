from pydantic import BaseModel,EmailStr,Field
from typing import Optional

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
    txn_type: str   # "credit" or "debit"
    description: str | None = None


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    amount: float
    txn_type: str
    description: str | None = None

    model_config = {
        "from_attributes": True
    }
