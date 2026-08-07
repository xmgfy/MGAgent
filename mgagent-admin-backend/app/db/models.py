from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

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

class AdminSession(Base):
    __tablename__ = "admin_sessions"
    
    id = Column(String(64), primary_key=True, index=True)
    admin_id = Column(String(64), ForeignKey("admins.id"), nullable=False)
    token = Column(String(512), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    admin = relationship("Admin", back_populates="sessions")

class Provider(Base):
    """模型提供商注册表 - 混合来源：种子预置 + 用户自定义"""
    __tablename__ = "providers"

    id = Column(String(64), primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    favicon_domain = Column(String(200), nullable=True)
    default_api_base = Column(String(300), nullable=True)
    supports_api_key = Column(Boolean, default=True)
    supports_local = Column(Boolean, default=False)
    supports_discover = Column(Boolean, default=True)
    supported_model_types = Column(Text, nullable=False)  # JSON 字符串, e.g. ["chat","embedding"]
    fallback_models = Column(Text, nullable=True)  # JSON 字符串
    description = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)  # Provider 级全局 API Key（可选默认值）
    is_system = Column(Boolean, default=False)  # True=内置不可删
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    model_type = Column(String(20), nullable=False, default="chat")
    provider = Column(String(50), nullable=False, default="openai")
    api_key = Column(String(500), nullable=True)
    api_base = Column(String(300), nullable=True)
    model_name = Column(String(100), nullable=False)
    dimension = Column(Integer, nullable=True)
    is_local = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    tenant_id = Column(String(64), nullable=True, index=True)  # NULL = 全局默认
    scenario = Column(String(50), nullable=True, index=True)  # chat/rag/code/default 等
    temperature = Column(Float, nullable=True)  # default 由工厂决定 (chat=0.7, rag=0.1)
    top_p = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    presence_penalty = Column(Float, nullable=True)
    frequency_penalty = Column(Float, nullable=True)
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
    storage_path = Column(String(500), nullable=True)  # MinIO 对象名或本地路径
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


class SecurityRule(Base):
    """安全规则表 - LLM输出敏感信息过滤配置"""
    __tablename__ = "security_rules"
    
    id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), ForeignKey("tenants.id"), nullable=True, index=True)
    rule_type = Column(String(20), nullable=False)  # 'keyword', 'regex'
    content = Column(Text, nullable=False)
    action = Column(String(20), nullable=False, default='mask')  # 'block', 'mask'
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    tenant = relationship("Tenant")


class EmbeddingConfig(Base):
    """Embedding 模型配置表 - 保证索引和查询使用同一模型"""
    __tablename__ = "embedding_configs"
    
    id = Column(String(64), primary_key=True, index=True)
    provider = Column(String(50), nullable=False)  # openai, zhipu, dashscope, jina, custom
    model_name = Column(String(100), nullable=False)
    api_key = Column(String(500), nullable=False)
    api_base = Column(String(300), nullable=False)
    dimension = Column(Integer, nullable=False, default=1536)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
