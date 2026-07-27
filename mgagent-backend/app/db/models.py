from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="active")
    max_users = Column(Integer, default=100)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    admins = relationship("Admin", back_populates="tenant")
    users = relationship("User", back_populates="tenant")

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="tenant_admin")
    tenant_id = Column(String(64), ForeignKey("tenants.id"), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    tenant = relationship("Tenant", back_populates="admins")
    sessions = relationship("AdminSession", back_populates="admin", cascade="all, delete-orphan")

class AdminSession(Base):
    __tablename__ = "admin_sessions"
    
    id = Column(String(64), primary_key=True, index=True)
    admin_id = Column(String(64), ForeignKey("admins.id"), nullable=False)
    token = Column(String(512), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    admin = relationship("Admin", back_populates="sessions")

class ModelConfig(Base):
    __tablename__ = "model_configs"
    
    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    api_key = Column(String(500), nullable=False)
    api_base = Column(String(200), nullable=False)
    model_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class SystemNotification(Base):
    __tablename__ = "system_notifications"
    
    id = Column(String(64), primary_key=True, index=True)
    type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    admin_id = Column(String(64), ForeignKey("admins.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    admin = relationship("Admin")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    status = Column(String(20), default="pending")
    tenant_id = Column(String(64), ForeignKey("tenants.id"), nullable=True)
    chat_count = Column(Integer, default=0)
    max_chats = Column(Integer, default=3)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    tenant = relationship("Tenant", back_populates="users")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"))
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", back_populates="sessions")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.id"))
    role = Column(String(20), index=True)
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    session = relationship("ChatSession", back_populates="messages")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(200), index=True)
    file_type = Column(String(20))
    file_size = Column(Integer)
    status = Column(String(20), default="uploaded")
    tenant_id = Column(String(64), ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    tenant = relationship("Tenant")

class AnonymousStats(Base):
    __tablename__ = "anonymous_stats"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_count = Column(Integer, default=0)
    max_chats = Column(Integer, default=3)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
