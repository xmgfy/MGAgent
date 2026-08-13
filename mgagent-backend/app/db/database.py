"""
数据库工厂 - Backend (MySQL only)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.config import settings, get_database_url
from .models import Base
from typing import Generator

engine = None
SessionLocal = None


def _create_mysql_engine():
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG,
    )


def init_engine():
    """初始化数据库引擎"""
    global engine, SessionLocal
    engine = _create_mysql_engine()
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    return engine


def init_db():
    """初始化数据库表结构"""
    global engine
    if engine is None:
        engine = init_engine()
    Base.metadata.create_all(bind=engine)
    _migrate_knowledge_base(engine)


def _migrate_knowledge_base(bind) -> None:
    """补齐旧库 documents.knowledge_base_id 列（幂等）"""
    try:
        from sqlalchemy import inspect, text
        insp = inspect(bind)
        if insp.has_table("documents"):
            columns = {col["name"] for col in insp.get_columns("documents")}
            if "knowledge_base_id" not in columns:
                bind.execute(text(
                    "ALTER TABLE documents ADD COLUMN knowledge_base_id VARCHAR(64) DEFAULT NULL"
                ))
                bind.commit()
                print("[migrate] added documents.knowledge_base_id column")
        print("[migrate] knowledge_base migration complete")
    except Exception as e:
        print(f"[migrate] knowledge_base migration failed (non-fatal): {e}")


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
