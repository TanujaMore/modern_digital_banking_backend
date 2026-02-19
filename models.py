from sqlalchemy import (
    Column, Integer, String, Boolean, Float,
    ForeignKey, Numeric, DateTime, Date, Text
)
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
from datetime import datetime


# =========================
# USER
# =========================
class User(Base):
    __tablename__ = "users"   # ✅ FIXED

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=True)
    two_factor_enabled = Column(Boolean, default=False)
    profile_image = Column(String, nullable=True) 

    accounts = relationship("Account", back_populates="user", cascade="all, delete")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete")
    bills = relationship("Bill", back_populates="user", cascade="all, delete")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete")


# =========================
# ACCOUNT
# =========================
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    balance = Column(Float, default=0.0)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
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
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    description = Column(String(255))
    merchant = Column(String(150))
    category = Column(String(100))

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    txn_type = Column(String(20), nullable=False)
    txn_date = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")


# =========================
# CATEGORY
# =========================
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    keywords = Column(String)


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
    spent_amount = Column(Float, default=0.0)

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
    amount_due = Column(Float, nullable=False)

    status = Column(String(20), default="upcoming")
    auto_pay = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bills")


# =========================
# REWARD
# =========================
class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    program_name = Column(String, nullable=False)
    points_balance = Column(Integer, default=0)

    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User")


# =========================
# ALERT
# =========================
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    alert_type = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)

    severity = Column(String(20), default="warning")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alerts")


# =========================
# TICKET
# =========================
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    subject = Column(String(255), nullable=False)
    description = Column(String, nullable=False)
    category = Column(String(100), nullable=False)

    status = Column(String, default="open")
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")

