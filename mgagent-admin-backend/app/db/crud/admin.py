from sqlalchemy.orm import Session
from app.db.models import Admin, Tenant
from datetime import datetime
import uuid
import bcrypt

def create_admin(db: Session, username: str, email: str, password: str, role: str = "tenant_admin", tenant_id: str = None) -> Admin:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin = Admin(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
        tenant_id=tenant_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

def get_admin_by_username(db: Session, username: str) -> Admin:
    return db.query(Admin).filter(Admin.username == username).first()

def get_admin_by_email(db: Session, email: str) -> Admin:
    return db.query(Admin).filter(Admin.email == email).first()

def get_admin_by_id(db: Session, admin_id: str) -> Admin:
    return db.query(Admin).filter(Admin.id == admin_id).first()

def get_admins(db: Session, tenant_id: str = None, role: str = None) -> list[Admin]:
    query = db.query(Admin)
    if tenant_id:
        query = query.filter(Admin.tenant_id == tenant_id)
    if role:
        query = query.filter(Admin.role == role)
    return query.all()

def update_admin(db: Session, admin_id: str, **kwargs) -> Admin:
    admin = get_admin_by_id(db, admin_id)
    if admin:
        for key, value in kwargs.items():
            setattr(admin, key, value)
        admin.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(admin)
    return admin

def delete_admin(db: Session, admin_id: str) -> bool:
    admin = get_admin_by_id(db, admin_id)
    if admin:
        db.delete(admin)
        db.commit()
        return True
    return False

def verify_admin_password(admin: Admin, password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), admin.hashed_password.encode('utf-8'))
