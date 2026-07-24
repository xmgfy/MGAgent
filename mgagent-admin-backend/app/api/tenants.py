from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.crud.tenant import create_tenant, get_tenants, get_tenant_by_id, update_tenant, delete_tenant
from app.db.crud.admin import create_admin
from app.db.models import Admin
from .auth import get_platform_admin

router = APIRouter()

class TenantCreateRequest(BaseModel):
    name: str
    description: str = None
    max_users: int = 100

class TenantUpdateRequest(BaseModel):
    name: str = None
    description: str = None
    max_users: int = None
    status: str = None

class TenantResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    max_users: int
    admin_count: int
    user_count: int
    created_at: str

@router.post("/tenants")
async def create_tenant_endpoint(
    request: TenantCreateRequest,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    if get_tenant_by_id(db, request.name):
        raise HTTPException(status_code=400, detail="租户名称已存在")
    
    tenant = create_tenant(db, request.name, request.description, request.max_users)
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "description": tenant.description,
        "status": tenant.status,
        "max_users": tenant.max_users,
        "created_at": tenant.created_at.isoformat()
    }

@router.get("/tenants", response_model=List[TenantResponse])
async def get_tenants_endpoint(
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    tenants = get_tenants(db)
    
    results = []
    for tenant in tenants:
        admin_count = len(tenant.admins)
        user_count = len(tenant.users)
        results.append({
            "id": tenant.id,
            "name": tenant.name,
            "description": tenant.description,
            "status": tenant.status,
            "max_users": tenant.max_users,
            "admin_count": admin_count,
            "user_count": user_count,
            "created_at": tenant.created_at.isoformat()
        })
    
    return results

@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant_endpoint(
    tenant_id: str,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    tenant = get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    admin_count = len(tenant.admins)
    user_count = len(tenant.users)
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "description": tenant.description,
        "status": tenant.status,
        "max_users": tenant.max_users,
        "admin_count": admin_count,
        "user_count": user_count,
        "created_at": tenant.created_at.isoformat()
    }

@router.put("/tenants/{tenant_id}")
async def update_tenant_endpoint(
    tenant_id: str,
    request: TenantUpdateRequest,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    tenant = get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.description is not None:
        update_data["description"] = request.description
    if request.max_users is not None:
        update_data["max_users"] = request.max_users
    if request.status is not None:
        update_data["status"] = request.status
    
    updated_tenant = update_tenant(db, tenant_id, **update_data)
    
    return {
        "id": updated_tenant.id,
        "name": updated_tenant.name,
        "description": updated_tenant.description,
        "status": updated_tenant.status,
        "max_users": updated_tenant.max_users,
        "created_at": updated_tenant.created_at.isoformat()
    }

@router.delete("/tenants/{tenant_id}")
async def delete_tenant_endpoint(
    tenant_id: str,
    admin: Admin = Depends(get_platform_admin),
    db: Session = Depends(get_db)
):
    tenant = get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    if delete_tenant(db, tenant_id):
        return {"message": "租户已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")
