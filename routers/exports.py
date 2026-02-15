from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from io import StringIO
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

from database import get_db
from auth import get_current_user
from models import User, Transaction, Account

router = APIRouter(
    prefix="/exports",
    tags=["Exports"]
)

# =====================================================
# EXPORT TRANSACTIONS AS CSV
# =====================================================
@router.get("/transactions/csv")
def export_transactions_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transactions = (
        db.query(Transaction)
        .join(Account)
        .filter(Account.user_id == current_user.id)
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)

    # CSV HEADER
    writer.writerow([
        "Transaction ID",
        "Account ID",
        "Type",
        "Amount",
        "Category",
        "Merchant",
        "Date"
    ])

    for txn in transactions:
        writer.writerow([
            txn.id,
            txn.account_id,
            txn.txn_type,
            float(txn.amount),
            txn.category,
            txn.merchant,
            txn.txn_date.strftime("%Y-%m-%d") if txn.txn_date else ""
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=transactions.csv"
        }
    )

# =====================================================
# EXPORT TRANSACTIONS AS PDF
# =====================================================
@router.get("/transactions/pdf")
def export_transactions_pdf(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # ✅ ensure folder exists
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)

    file_path = os.path.join(
        export_dir,
        f"transactions_{current_user.id}.pdf"
    )

    transactions = (
        db.query(Transaction)
        .join(Account)
        .filter(Account.user_id == current_user.id)
        .all()
    )

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Transaction Report")

    y -= 30

    for txn in transactions:
        text = f"{txn.txn_date.date()} | {txn.description} | {txn.amount} | {txn.txn_type}"
        c.drawString(50, y, text)
        y -= 15

        if y < 50:
            c.showPage()
            y = height - 50

    c.save()

    return FileResponse(
        path=file_path,
        filename=f"transactions_{current_user.id}.pdf",
        media_type="application/pdf"
    )
