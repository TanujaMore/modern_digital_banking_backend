from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Ticket, User
from schemas import TicketCreate, TicketResponse
from deps import get_current_user

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# =========================
# CREATE TICKET
# =========================
@router.post("/", response_model=TicketResponse)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_ticket = Ticket(
        user_id=current_user.id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        status="open"
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


# =========================
# GET USER TICKETS
# =========================
@router.get("/", response_model=List[TicketResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return tickets