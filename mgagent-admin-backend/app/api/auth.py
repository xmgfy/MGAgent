from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import jwt
import bcrypt
from datetime import datetime, timedelta
from app.db.database import get_db
from app.db.crud.admin import get_admin_by_username, verify_admin_password, create_admin, update_admin
from app.db.crud.tenant import create_tenant
from app.db.models import Admin

router = APIRouter()

SECRET_KEY = "mgagent_admin_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    tenant_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    admin: dict

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权访问")
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(status_code=401, detail="无效的令牌")
        
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise HTTPException(status_code=401, detail="管理员不存在")
        
        if admin.status == "disabled":
            raise HTTPException(status_code=401, detail="管理员账号已被禁用")
        
        return admin
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

async def get_platform_admin(admin: Admin = Depends(get_current_admin)):
    if admin.role != "platform_admin":
        raise HTTPException(status_code=403, detail="需要平台管理员权限")
    return admin

async def get_tenant_admin(admin: Admin = Depends(get_current_admin)):
    if admin.role != "tenant_admin":
        raise HTTPException(status_code=403, detail="需要租户管理员权限")
    return admin

@router.post("/auth/login", response_model=TokenResponse)
async def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = get_admin_by_username(db, request.username)
    
    if not admin:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not verify_admin_password(admin, request.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if admin.status == "disabled":
        raise HTTPException(status_code=401, detail="管理员账号已被禁用")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.id}, expires_delta=access_token_expires
    )
    
    status_message = ""
    if admin.status == "frozen":
        status_message = "管理员账号已被冻结，请联系平台管理员解冻"
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        admin={
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "role": admin.role,
            "tenant_id": admin.tenant_id,
            "status": admin.status,
            "status_message": status_message
        }
    )

@router.post("/auth/register")
async def admin_register(request: AdminRegisterRequest, db: Session = Depends(get_db)):
    if get_admin_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    if get_admin_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    tenant_id = None
    if request.tenant_name:
        tenant = create_tenant(db, name=request.tenant_name)
        tenant_id = tenant.id
    
    admin = create_admin(db, request.username, request.email, request.password, "tenant_admin", tenant_id)
    
    return {
        "message": "管理员注册成功",
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "role": admin.role,
            "tenant_id": admin.tenant_id,
            "created_at": admin.created_at.isoformat()
        }
    }

@router.get("/auth/me")
async def get_current_admin_info(admin: Admin = Depends(get_current_admin)):
    return {
        "id": admin.id,
        "username": admin.username,
        "email": admin.email,
        "role": admin.role,
        "tenant_id": admin.tenant_id,
        "status": admin.status,
        "created_at": admin.created_at.isoformat()
    }

class UpdateAdminProfileRequest(BaseModel):
    email: Optional[str] = None

class UpdateAdminPasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.put("/auth/profile")
async def update_admin_profile(
    request: UpdateAdminProfileRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    update_data = {}
    if request.email:
        existing = db.query(Admin).filter(Admin.email == request.email, Admin.id != admin.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        update_data["email"] = request.email
    
    updated_admin = update_admin(db, admin.id, **update_data)
    
    return {
        "id": updated_admin.id,
        "username": updated_admin.username,
        "email": updated_admin.email,
        "role": updated_admin.role,
        "tenant_id": updated_admin.tenant_id,
        "status": updated_admin.status,
        "created_at": updated_admin.created_at.isoformat(),
        "updated_at": updated_admin.updated_at.isoformat()
    }

@router.put("/auth/password")
async def update_admin_password(
    request: UpdateAdminPasswordRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if not verify_admin_password(admin, request.old_password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")
    
    hashed_password = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    update_admin(db, admin.id, hashed_password=hashed_password)
    
    return {"message": "密码更新成功"}

@router.post("/auth/logout")
async def admin_logout(admin: Admin = Depends(get_current_admin)):
    return {"message": "登出成功"}
