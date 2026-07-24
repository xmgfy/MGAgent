from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import psutil
import platform
import time
from app.db.database import get_db
from app.db.crud.notification import get_notifications, mark_notification_read, create_notification, get_unread_count
from app.db.models import Admin
from .auth import get_current_admin

router = APIRouter()

START_TIME = time.time()

class SystemStatus(BaseModel):
    status: str
    version: str
    uptime: str

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    is_read: bool
    created_at: str

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(admin: Admin = Depends(get_current_admin)):
    uptime_seconds = time.time() - START_TIME
    
    days = int(uptime_seconds // (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    
    if days > 0:
        uptime_str = f"{days}天 {hours}小时 {minutes}分钟"
    elif hours > 0:
        uptime_str = f"{hours}小时 {minutes}分钟 {seconds}秒"
    elif minutes > 0:
        uptime_str = f"{minutes}分钟 {seconds}秒"
    else:
        uptime_str = f"{seconds}秒"
    
    return SystemStatus(
        status="healthy",
        version="1.0.0",
        uptime=uptime_str
    )

@router.get("/system/info")
async def get_system_info(admin: Admin = Depends(get_current_admin)):
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent
    }

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications_endpoint(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    notifications = get_notifications(db, admin_id=admin.id)
    
    return [{
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "message": n.message,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat()
    } for n in notifications]

@router.get("/notifications/unread-count")
async def get_unread_notifications_count(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    count = get_unread_count(db, admin.id)
    return {"count": count}

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read_endpoint(
    notification_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    notification = mark_notification_read(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat()
    }

@router.post("/notifications")
async def create_notification_endpoint(
    type: str,
    title: str,
    message: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    notification = create_notification(db, type, title, message, admin.id)
    
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat()
    }

@router.post("/notifications/external")
async def create_external_notification(
    type: str,
    title: str,
    message: str,
    db: Session = Depends(get_db)
):
    from app.db.models import Admin
    
    platform_admins = db.query(Admin).filter(Admin.role == "platform_admin").all()
    
    if platform_admins:
        for admin in platform_admins:
            create_notification(db, type, title, message, admin.id)
        return {"message": f"通知已发送给 {len(platform_admins)} 位平台管理员"}
    else:
        notification = create_notification(db, type, title, message, None)
        return {
            "id": notification.id,
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat()
        }

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
