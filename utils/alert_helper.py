from sqlalchemy.exc import IntegrityError
from models import Alert


def create_alert(
    db,
    user_id: int,
    alert_type: str,
    message: str,
    severity: str = "warning",
    title: str | None = None
):
    """
    Safe alert creator.
    Never breaks transaction flow.
    Prevents duplicates.
    """

    # Prevent duplicate alerts
    existing = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.alert_type == alert_type,
        Alert.message == message
    ).first()

    if existing:
        return existing

    alert = Alert(
        user_id=user_id,
        alert_type=alert_type,
        title=title or alert_type.replace("_", " ").title(),
        message=message,
        severity=severity,
        is_read=False  
    )

    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    except IntegrityError:
        db.rollback()
        return None
    except Exception:
        # 🔥 MOST IMPORTANT: never break main flow
        db.rollback()
        return None
