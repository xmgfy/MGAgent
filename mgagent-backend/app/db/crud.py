from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import ChatSession, ChatMessage, Document, User, AnonymousStats
from datetime import datetime
import uuid
import bcrypt

def create_chat_session(db: Session, user_id: str, title: str = "新对话") -> ChatSession:
    session_id = str(uuid.uuid4())
    db_session = ChatSession(
        id=session_id,
        user_id=user_id,
        title=title
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_chat_session(db: Session, session_id: str) -> ChatSession:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()

def get_chat_sessions(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> list:
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()

def update_chat_session_title(db: Session, session_id: str, title: str) -> ChatSession:
    db_session = get_chat_session(db, session_id)
    if db_session:
        db_session.title = title
        db.commit()
        db.refresh(db_session)
    return db_session

def delete_chat_session(db: Session, session_id: str) -> bool:
    db_session = get_chat_session(db, session_id)
    if db_session:
        db.delete(db_session)
        db.commit()
        return True
    return False

def add_message(db: Session, session_id: str, role: str, content: str) -> ChatMessage:
    db_session = get_chat_session(db, session_id)
    if not db_session:
        db_session = create_chat_session(db, "default_user")
    
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(message)
    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return message

def get_messages(db: Session, session_id: str, skip: int = 0, limit: int = 100) -> list:
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()

def create_document(db: Session, filename: str, file_type: str, file_size: int) -> Document:
    document_id = str(uuid.uuid4())
    document = Document(
        id=document_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def get_document(db: Session, document_id: str) -> Document:
    return db.query(Document).filter(Document.id == document_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100) -> list:
    return db.query(Document).order_by(desc(Document.created_at)).offset(skip).limit(limit).all()

def update_document_status(db: Session, document_id: str, status: str) -> Document:
    document = get_document(db, document_id)
    if document:
        document.status = status
        db.commit()
        db.refresh(document)
    return document

def delete_document(db: Session, document_id: str) -> bool:
    document = get_document(db, document_id)
    if document:
        db.delete(document)
        db.commit()
        return True
    return False

def create_user(db: Session, username: str, email: str, password: str, role: str = "user") -> User:
    user_id = str(uuid.uuid4())
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        id=user_id,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
        status="pending",
        chat_count=0,
        max_chats=3
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: str) -> User:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100, status: str = None) -> list:
    query = db.query(User)
    if status:
        query = query.filter(User.status == status)
    return query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()

def update_user_status(db: Session, user_id: str, status: str) -> User:
    user = get_user(db, user_id)
    if user:
        user.status = status
        db.commit()
        db.refresh(user)
    return user

def update_user_role(db: Session, user_id: str, role: str) -> User:
    user = get_user(db, user_id)
    if user:
        user.role = role
        db.commit()
        db.refresh(user)
    return user

def increment_chat_count(db: Session, user_id: str) -> User:
    user = get_user(db, user_id)
    if user:
        user.chat_count += 1
        db.commit()
        db.refresh(user)
    return user

def get_anonymous_stats(db: Session) -> AnonymousStats:
    """获取或创建匿名用户统计记录"""
    stats = db.query(AnonymousStats).first()
    if not stats:
        stats = AnonymousStats(chat_count=0, max_chats=3)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats

def get_anonymous_chat_count(db: Session) -> int:
    """获取匿名用户的总聊天次数"""
    stats = get_anonymous_stats(db)
    return stats.chat_count or 0

def get_anonymous_max_chats(db: Session) -> int:
    """获取匿名用户的最大聊天次数限制"""
    stats = get_anonymous_stats(db)
    return stats.max_chats or 3

def increment_anonymous_chat_count(db: Session) -> int:
    """增加匿名用户的聊天次数并返回新的计数"""
    stats = get_anonymous_stats(db)
    stats.chat_count += 1
    stats.last_used_at = datetime.utcnow()
    db.commit()
    db.refresh(stats)
    return stats.chat_count

def verify_password(db: Session, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if user and bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        return user
    return None