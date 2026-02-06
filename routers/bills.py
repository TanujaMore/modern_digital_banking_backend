from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models import Bill
from schemas import BillCreate, BillUpdate, BillResponse, BillStatus
from auth import get_current_user

router = APIRouter(
    prefix="/bills",
    tags=["Bills"]
)

# =========================
# HELPER FUNCTIONS (ADDED)
# =========================
def calculate_overdue(due_date, status):
    return status != BillStatus.paid and date.today() > due_date


def calculate_status(due_date, status):
    if status == BillStatus.paid:
        return BillStatus.paid
    if date.today() > due_date:
        return BillStatus.overdue
    return BillStatus.upcoming


# =========================
# CREATE BILL
# =========================
@router.post("/", response_model=BillResponse)
def create_bill(
    bill: BillCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    new_bill = Bill(
        user_id=current_user.id,   # 🔧 FIX: always logged-in user
        biller_name=bill.biller_name,
        due_date=bill.due_date,
        amount_due=bill.amount_due,
        status=BillStatus.upcoming,
        auto_pay=bill.auto_pay
    )

    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)

    return {
        **new_bill.__dict__,
        "status": calculate_status(new_bill.due_date, new_bill.status),
        "overdue": calculate_overdue(new_bill.due_date, new_bill.status)
    }


# =========================
# LIST ALL BILLS
# =========================
@router.get("/", response_model=list[BillResponse])
def list_bills(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    bills = db.query(Bill).filter(
        Bill.user_id == current_user.id
    ).all()

    response = []
    for bill in bills:
        response.append({
            **bill.__dict__,
            "status": calculate_status(bill.due_date, bill.status),
            "overdue": calculate_overdue(bill.due_date, bill.status)
        })

    return response


# =========================
# UPDATE BILL (MARK PAID / EDIT)
# =========================
@router.put("/{bill_id}", response_model=BillResponse)
def update_bill(
    bill_id: int,
    bill_data: BillUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    bill = db.query(Bill).filter(
        Bill.id == bill_id,
        Bill.user_id == current_user.id
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    # 🔧 SAFE FIELD UPDATES
    if bill_data.biller_name is not None:
        bill.biller_name = bill_data.biller_name

    if bill_data.amount_due is not None:
        bill.amount_due = bill_data.amount_due

    if bill_data.due_date is not None:
        bill.due_date = bill_data.due_date

    if bill_data.status is not None:
        bill.status = bill_data.status

    if bill_data.auto_pay is not None:
        bill.auto_pay = bill_data.auto_pay

    db.commit()
    db.refresh(bill)

    return {
        **bill.__dict__,
        "status": calculate_status(bill.due_date, bill.status),
        "overdue": calculate_overdue(bill.due_date, bill.status)
    }


# =========================
# DELETE BILL
# =========================
@router.delete("/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    bill = db.query(Bill).filter(
        Bill.id == bill_id,
        Bill.user_id == current_user.id
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    db.delete(bill)
    db.commit()

    return {"message": "Bill deleted successfully"}
