from sqlalchemy.orm import Session
from app.db.models import SystemNotification
from datetime import datetime
import uuid

def create_notification(db: Session, type: str, title: str, message: str, admin_id: str = None) -> SystemNotification:
    notification = SystemNotification(
        id=str(uuid.uuid4()),
        type=type,
        title=title,
        message=message,
        admin_id=admin_id,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_notification_by_id(db: Session, notification_id: str) -> SystemNotification:
    return db.query(SystemNotification).filter(SystemNotification.id == notification_id).first()

def get_notifications(db: Session, admin_id: str = None, is_read: bool = None) -> list[SystemNotification]:
    query = db.query(SystemNotification)
    if admin_id:
        query = query.filter(SystemNotification.admin_id == admin_id)
    if is_read is not None:
        query = query.filter(SystemNotification.is_read == is_read)
    return query.order_by(SystemNotification.created_at.desc()).all()

def mark_notification_read(db: Session, notification_id: str) -> SystemNotification:
    notification = get_notification_by_id(db, notification_id)
    if notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification

def delete_notification(db: Session, notification_id: str) -> bool:
    notification = get_notification_by_id(db, notification_id)
    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False

def get_unread_count(db: Session, admin_id: str = None) -> int:
    query = db.query(SystemNotification).filter(SystemNotification.is_read == False)
    if admin_id:
        query = query.filter(SystemNotification.admin_id == admin_id)
    return query.count()
