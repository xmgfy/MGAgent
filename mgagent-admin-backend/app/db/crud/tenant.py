from sqlalchemy.orm import Session
from app.db.models import Tenant
from datetime import datetime
import uuid

def create_tenant(db: Session, name: str, description: str = None, max_users: int = 100) -> Tenant:
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        max_users=max_users,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

def get_tenant_by_id(db: Session, tenant_id: str) -> Tenant:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()

def get_tenant_by_name(db: Session, name: str) -> Tenant:
    return db.query(Tenant).filter(Tenant.name == name).first()

def get_tenants(db: Session) -> list[Tenant]:
    return db.query(Tenant).all()

def update_tenant(db: Session, tenant_id: str, **kwargs) -> Tenant:
    tenant = get_tenant_by_id(db, tenant_id)
    if tenant:
        for key, value in kwargs.items():
            setattr(tenant, key, value)
        tenant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tenant)
    return tenant

def delete_tenant(db: Session, tenant_id: str) -> bool:
    tenant = get_tenant_by_id(db, tenant_id)
    if tenant:
        db.delete(tenant)
        db.commit()
        return True
    return False
