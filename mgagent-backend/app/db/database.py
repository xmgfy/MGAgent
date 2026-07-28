"""
数据库工厂 - 根据方案创建对应的数据库连接
支持 SQLite 和 MySQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config.config import (
    settings,
    is_sqlite_scheme,
    is_mysql_scheme,
    get_database_url,
    get_sqlite_path,
    BASE_DIR
)
from .models import Base
from typing import Generator

# 全局变量
engine = None
SessionLocal = None

def _create_sqlite_engine():
    """创建 SQLite 引擎"""
    sqlite_path = get_sqlite_path()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    
    return create_engine(
        get_database_url(),
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )

def _create_mysql_engine():
    """创建 MySQL 引擎"""
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG
    )

def init_engine():
    """初始化数据库引擎"""
    global engine, SessionLocal
    
    if is_mysql_scheme():
        engine = _create_mysql_engine()
    else:
        engine = _create_sqlite_engine()
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    return engine

def init_db():
    """初始化数据库表结构"""
    global engine
    if engine is None:
        engine = init_engine()
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的依赖函数"""
    global SessionLocal
    if SessionLocal is None:
        init_engine()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session(db: Session = None) -> Session:
    """获取或创建数据库会话"""
    if db:
        return db
    return next(get_db())

def get_engine():
    """获取当前引擎"""
    global engine
    if engine is None:
        engine = init_engine()
    return engine
