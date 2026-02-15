from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta

from database import get_db
from models import Bill, Alert
from schemas import BillCreate, BillUpdate, BillResponse, BillStatus
from auth import get_current_user
from utils.alert_helper import create_alert

router = APIRouter(
    prefix="/bills",
    tags=["Bills"]
)

# =========================
# HELPER FUNCTIONS
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
        user_id=current_user.id,
        biller_name=bill.biller_name,
        due_date=bill.due_date,
        amount_due=bill.amount_due,
        status=BillStatus.upcoming,
        auto_pay=bill.auto_pay
    )

    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)

    status = calculate_status(new_bill.due_date, new_bill.status)

    return {
        **new_bill.__dict__,
        "status": status,
        "overdue": calculate_overdue(new_bill.due_date, status)
    }


# =========================
# LIST BILLS + SAFE ALERT
# =========================
@router.get("/", response_model=list[BillResponse])
def list_bills(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    bills = db.query(Bill).filter(
        Bill.user_id == current_user.id
    ).all()

    today_plus_3 = date.today() + timedelta(days=3)
    response = []

    for bill in bills:
        current_status = calculate_status(bill.due_date, bill.status)

        # 🔔 BILL DUE ALERT (NO DUPLICATES)
        if current_status != BillStatus.paid and bill.due_date <= today_plus_3:
            existing_alert = db.query(Alert).filter(
                Alert.user_id == current_user.id,
                Alert.alert_type == "bill_due",
                Alert.message == f"{bill.biller_name} bill due on {bill.due_date}"
            ).first()

            if not existing_alert:
                create_alert(
                    db=db,
                    user_id=current_user.id,
                    title="Bill Due Reminder",
                    alert_type="bill_due",
                    message=f"{bill.biller_name} bill due on {bill.due_date}",
                    severity="info"
                )

        response.append({
            **bill.__dict__,
            "status": current_status,
            "overdue": calculate_overdue(bill.due_date, current_status)
        })

    db.commit()
    return response


# =========================
# UPDATE BILL
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

    status = calculate_status(bill.due_date, bill.status)

    return {
        **bill.__dict__,
        "status": status,
        "overdue": calculate_overdue(bill.due_date, status)
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

    # 🧹 Optional cleanup: remove related bill alerts
    db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.alert_type == "bill_due",
        Alert.message.contains(bill.biller_name)
    ).delete(synchronize_session=False)

    db.delete(bill)
    db.commit()

    return {"message": "Bill deleted successfully"}
