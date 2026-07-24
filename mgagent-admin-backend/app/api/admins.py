from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.database import get_db
from app.db.crud.admin import get_admins, get_admin_by_id, update_admin, delete_admin, create_admin, get_admin_by_username, get_admin_by_email
from app.db.models import Admin
from .auth import get_current_admin, get_platform_admin

router = APIRouter()

class CreateAdminRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "tenant_admin"
    tenant_id: Optional[str] = None

class UpdateAdminRequest(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None
    status: Optional[str] = None

class AdminResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    tenant_id: Optional[str]
    tenant_name: Optional[str]
    status: str
    created_at: str
    updated_at: str

@router.get("/admins", response_model=List[AdminResponse])
async def get_admins_list(
    role: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    admins = get_admins(db, tenant_id=tenant_id, role=role)
    
    results = []
    for admin_item in admins:
        tenant_name = None
        if admin_item.tenant:
            tenant_name = admin_item.tenant.name
        
        results.append({
            "id": admin_item.id,
            "username": admin_item.username,
            "email": admin_item.email,
            "role": admin_item.role,
            "tenant_id": admin_item.tenant_id,
            "tenant_name": tenant_name,
            "status": admin_item.status,
            "created_at": admin_item.created_at.isoformat(),
            "updated_at": admin_item.updated_at.isoformat()
        })
    
    return results

@router.get("/admins/{admin_id}", response_model=AdminResponse)
async def get_admin_endpoint(
    admin_id: str,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    admin_item = get_admin_by_id(db, admin_id)
    if not admin_item:
        raise HTTPException(status_code=404, detail="管理员不存在")
    
    tenant_name = None
    if admin_item.tenant:
        tenant_name = admin_item.tenant.name
    
    return {
        "id": admin_item.id,
        "username": admin_item.username,
        "email": admin_item.email,
        "role": admin_item.role,
        "tenant_id": admin_item.tenant_id,
        "tenant_name": tenant_name,
        "status": admin_item.status,
        "created_at": admin_item.created_at.isoformat(),
        "updated_at": admin_item.updated_at.isoformat()
    }

@router.post("/admins")
async def create_admin_endpoint(
    request: CreateAdminRequest,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    if get_admin_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    if get_admin_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    if request.role not in ["platform_admin", "tenant_admin"]:
        raise HTTPException(status_code=400, detail="无效的角色值")
    
    if request.role == "platform_admin":
        existing_platform_admin = db.query(Admin).filter(Admin.role == "platform_admin").first()
        if existing_platform_admin:
            raise HTTPException(status_code=400, detail="平台管理员只能有一个")
    
    if request.role == "tenant_admin" and not request.tenant_id:
        raise HTTPException(status_code=400, detail="租户管理员必须分配租户")
    
    admin_item = create_admin(db, request.username, request.email, request.password, request.role, request.tenant_id)
    
    tenant_name = None
    if admin_item.tenant:
        tenant_name = admin_item.tenant.name
    
    return {
        "id": admin_item.id,
        "username": admin_item.username,
        "email": admin_item.email,
        "role": admin_item.role,
        "tenant_id": admin_item.tenant_id,
        "tenant_name": tenant_name,
        "status": admin_item.status,
        "created_at": admin_item.created_at.isoformat(),
        "updated_at": admin_item.updated_at.isoformat()
    }

@router.put("/admins/{admin_id}")
async def update_admin_endpoint(
    admin_id: str,
    request: UpdateAdminRequest,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    admin_item = get_admin_by_id(db, admin_id)
    if not admin_item:
        raise HTTPException(status_code=404, detail="管理员不存在")
    
    if admin_item.role == "platform_admin" and admin_id != admin.id:
        raise HTTPException(status_code=403, detail="无权修改平台管理员")
    
    update_data = {}
    if request.email is not None:
        existing = db.query(Admin).filter(Admin.email == request.email, Admin.id != admin_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        update_data["email"] = request.email
    
    if request.role is not None:
        if request.role not in ["platform_admin", "tenant_admin"]:
            raise HTTPException(status_code=400, detail="无效的角色值")
        update_data["role"] = request.role
    
    if request.tenant_id is not None:
        update_data["tenant_id"] = request.tenant_id
    
    if request.status is not None:
        if request.status not in ["active", "disabled", "frozen"]:
            raise HTTPException(status_code=400, detail="无效的状态值")
        
        if request.status in ["disabled", "frozen"] and admin_id == admin.id:
            raise HTTPException(status_code=400, detail="不能冻结或禁用自己的管理员账号")
        
        update_data["status"] = request.status
    
    updated_admin = update_admin(db, admin_id, **update_data)
    
    tenant_name = None
    if updated_admin.tenant:
        tenant_name = updated_admin.tenant.name
    
    return {
        "id": updated_admin.id,
        "username": updated_admin.username,
        "email": updated_admin.email,
        "role": updated_admin.role,
        "tenant_id": updated_admin.tenant_id,
        "tenant_name": tenant_name,
        "status": updated_admin.status,
        "created_at": updated_admin.created_at.isoformat(),
        "updated_at": updated_admin.updated_at.isoformat()
    }

@router.delete("/admins/{admin_id}")
async def delete_admin_endpoint(
    admin_id: str,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    admin_item = get_admin_by_id(db, admin_id)
    if not admin_item:
        raise HTTPException(status_code=404, detail="管理员不存在")
    
    if admin_item.role == "platform_admin":
        raise HTTPException(status_code=403, detail="无法删除平台管理员")
    
    if delete_admin(db, admin_id):
        return {"message": "管理员已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")