from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.notification_log import NotificationLog

router = APIRouter(prefix="/api/notifications", tags=["Уведомления"])

@router.get("", summary="История уведомлений")
def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    logs = session.exec(
        select(NotificationLog)
        .order_by(NotificationLog.created_at.desc())
        .limit(limit)
    ).all()
    return [{"id": l.id, "user_id": l.user_id, "username": l.username,
             "event_type": l.event_type, "message": l.message,
             "order_id": l.order_id,
             "created_at": l.created_at.isoformat() if l.created_at else None}
            for l in logs]

def add_notification(session, user_id, username, event_type, message, order_id=None):
    try:
        from models.notification_log import NotificationLog
        log = NotificationLog(user_id=user_id, username=username, event_type=event_type,
                              message=message, order_id=order_id)
        session.add(log); session.commit()
    except: pass
