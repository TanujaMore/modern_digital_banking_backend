from sqlalchemy import Column, Integer, String, Float, ForeignKey,Numeric,DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    
    accounts = relationship("Account", back_populates="user")
    budgets = relationship("Budget", back_populates="user")



class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    account_type=Column(String,nullable=False)
    balance = Column(Float, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account",cascade="all,delete")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    description = Column(String(255))

    merchant = Column(String(150))        # 🔥 MUST BE THIS NAME
    category = Column(String(100))
    amount = Column(Numeric(12, 2))
    currency = Column(String(3))          # 🔥 MUST BE THIS NAME
    txn_type = Column(String(50))
    txn_date = Column(DateTime, nullable=True, default=datetime.utcnow)
    account = relationship("Account", back_populates="transactions")



class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    keywords = Column(String)   # comma separated keywords


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    category = Column(String, nullable=False)
    limit_amount = Column(Float, nullable=False)
    spent_amount = Column(Float, default=0)

    user = relationship("User", back_populates="budgets")
