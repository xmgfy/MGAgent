from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.database import get_db
from app.db.crud.user import get_users, get_user_by_id, update_user, delete_user
from app.db.crud.admin import get_admin_by_id
from app.db.models import Admin, User
from .auth import get_current_admin, get_platform_admin, get_tenant_admin

router = APIRouter()

class UpdateUserStatusRequest(BaseModel):
    status: str

class UpdateUserRoleRequest(BaseModel):
    role: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    status: str
    tenant_id: str
    chat_count: int
    max_chats: int
    created_at: str

@router.get("/users", response_model=List[UserResponse])
async def get_users_list(
    status: Optional[str] = Query(None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    tenant_id = None
    if admin.role == "tenant_admin":
        tenant_id = admin.tenant_id
    
    users = get_users(db, tenant_id=tenant_id, status=status)
    
    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "status": u.status,
        "tenant_id": u.tenant_id,
        "chat_count": u.chat_count,
        "max_chats": u.max_chats,
        "created_at": u.created_at.isoformat()
    } for u in users]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if admin.role == "tenant_admin" and user.tenant_id != admin.tenant_id:
        raise HTTPException(status_code=403, detail="无权访问该用户")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "tenant_id": user.tenant_id,
        "chat_count": user.chat_count,
        "max_chats": user.max_chats,
        "created_at": user.created_at.isoformat()
    }

@router.put("/users/{user_id}/status")
async def update_user_status_endpoint(
    user_id: str,
    request: UpdateUserStatusRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if admin.role == "tenant_admin" and user.tenant_id != admin.tenant_id:
        raise HTTPException(status_code=403, detail="无权操作该用户")
    
    if request.status not in ["pending", "approved", "frozen", "disabled"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    updated_user = update_user(db, user_id, status=request.status)
    
    return {
        "id": updated_user.id,
        "username": updated_user.username,
        "email": updated_user.email,
        "role": updated_user.role,
        "status": updated_user.status,
        "tenant_id": updated_user.tenant_id,
        "chat_count": updated_user.chat_count,
        "max_chats": updated_user.max_chats,
        "created_at": updated_user.created_at.isoformat()
    }

@router.put("/users/{user_id}/role")
async def update_user_role_endpoint(
    user_id: str,
    request: UpdateUserRoleRequest,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if request.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="无效的角色值")
    
    updated_user = update_user(db, user_id, role=request.role)
    
    return {
        "id": updated_user.id,
        "username": updated_user.username,
        "email": updated_user.email,
        "role": updated_user.role,
        "status": updated_user.status,
        "tenant_id": updated_user.tenant_id,
        "chat_count": updated_user.chat_count,
        "max_chats": updated_user.max_chats,
        "created_at": updated_user.created_at.isoformat()
    }

@router.delete("/users/{user_id}")
async def delete_user_endpoint(
    user_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if admin.role == "tenant_admin" and user.tenant_id != admin.tenant_id:
        raise HTTPException(status_code=403, detail="无权删除该用户")
    
    if delete_user(db, user_id):
        return {"message": "用户已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")
