from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
from .models import Base

# MySQL 连接配置
DATABASE_URL = settings.DATABASE_URL

# 创建引擎，添加 MySQL 特定配置
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 自动检测断开的连接
    pool_recycle=3600,  # 每小时回收连接
    pool_size=10,       # 连接池大小
    max_overflow=20,    # 最大溢出连接数
    echo=settings.DEBUG  # 调试模式下打印 SQL
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db():
    """初始化数据库表结构"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session(db: Session = None):
    """获取或创建数据库会话"""
    if db:
        return db
    return next(get_db())
