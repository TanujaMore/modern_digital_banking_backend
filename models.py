from sqlalchemy import (
    Column, Integer, String, Boolean, Float,
    ForeignKey, Numeric, DateTime,Date
)
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
from datetime import datetime


# =========================
# USER
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=True)  # ✅ ADD THIS
    accounts = relationship("Account", back_populates="user", cascade="all, delete")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete")
    bills = relationship("Bill", back_populates="user", cascade="all, delete")  # ✅ FIXED


# =========================
# ACCOUNT
# =========================
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    balance = Column(Float, default=0)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="accounts")

    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete"
    )


# =========================
# TRANSACTION
# =========================
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))

    description = Column(String(255))
    merchant = Column(String(150))
    category = Column(String(100))
    amount = Column(Numeric(12, 2))
    currency = Column(String(3))
    txn_type = Column(String(50))
    txn_date = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")


# =========================
# CATEGORY
# =========================
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    keywords = Column(String)  # comma-separated


# =========================
# BUDGET
# =========================
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


# =========================
# BILL
# =========================
class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    biller_name = Column(String(150), nullable=False)
    due_date = Column(Date, nullable=False)
    amount_due = Column(Numeric(12, 2), nullable=False)

    status = Column(String, default="pending")  # or Enum if defined
    auto_pay = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="bills")  # ✅ FIXED



class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    program_name = Column(String, nullable=False)
    points_balance = Column(Integer, default=0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    