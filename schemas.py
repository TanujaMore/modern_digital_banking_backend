from pydantic import BaseModel

class RegisterUser(BaseModel):
    name: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AccountCreate(BaseModel):
    bank_name: str
    account_type: str
    balance: float = 0

class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    type: str