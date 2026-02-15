from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import AlertOut
from auth import get_current_user
from models import Alert
from utils.alert_helper import create_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# =================================================
# GET ALERTS (ALL / READ / UNREAD)
# =================================================
@router.get("/", response_model=list[AlertOut])
def get_alerts(
    status: str | None = None,   # all | read | unread
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Alert).filter(
        Alert.user_id == current_user.id
    )

    if status == "read":
        query = query.filter(Alert.is_read == True)
    elif status == "unread":
        query = query.filter(Alert.is_read == False)

    return query.order_by(Alert.created_at.desc()).all()


# =================================================
# MARK ALERT READ / UNREAD (TOGGLE)
# =================================================
@router.put("/{alert_id}/toggle")
def toggle_alert_status(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = not alert.is_read
    db.commit()

    return {"message": "Alert status updated"}


# =================================================
# UNREAD ALERT COUNT (🔔 BELL)
# =================================================
@router.get("/unread-count")
def unread_alert_count(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    count = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).count()

    return {"unread": count}


# =================================================
# LATEST ALERTS (FOR BELL DROPDOWN)
# =================================================
@router.get("/latest", response_model=list[AlertOut])
def latest_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return (
        db.query(Alert)
        .filter(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )


# =================================================
# CREATE TEST ALERT (YOUR EXISTING LOGIC – KEPT)
# =================================================
@router.post("/test")
def create_test_alert(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    create_alert(
        db=db,
        user_id=current_user.id,
        title="Test Alert",
        alert_type="TEST",
        message="This is a test alert 🔔",
        severity="info"
    )

    db.commit()
    return {"message": "Test alert created"}
