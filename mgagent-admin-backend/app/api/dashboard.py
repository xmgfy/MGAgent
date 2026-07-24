from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Admin, User, ChatMessage, ChatSession
from .auth import get_current_admin

router = APIRouter()

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(ChatMessage).filter(ChatMessage.role == 'assistant')
        if admin.role == "tenant_admin" and admin.tenant_id:
            query = query.join(ChatSession).join(User).filter(User.tenant_id == admin.tenant_id)
        model_calls = query.count()
        
        query = db.query(ChatSession)
        if admin.role == "tenant_admin" and admin.tenant_id:
            query = query.join(User).filter(User.tenant_id == admin.tenant_id)
        total_sessions = query.count()
        
        query = db.query(User)
        if admin.role == "tenant_admin" and admin.tenant_id:
            query = query.filter(User.tenant_id == admin.tenant_id)
        total_users = query.count()
        
        return {
            "model_calls": model_calls,
            "total_sessions": total_sessions,
            "total_users": total_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
