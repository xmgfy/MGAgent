from sqlalchemy.orm import Session
from app.db.models import User
from datetime import datetime
import uuid
import bcrypt

def create_user(db: Session, username: str, email: str, password: str, tenant_id: str = None) -> User:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password=hashed_password,
        tenant_id=tenant_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str) -> User:
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, tenant_id: str = None, status: str = None) -> list[User]:
    query = db.query(User)
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    if status:
        query = query.filter(User.status == status)
    return query.all()

def update_user(db: Session, user_id: str, **kwargs) -> User:
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in kwargs.items():
            setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: str) -> bool:
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def verify_user_password(user: User, password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8'))
