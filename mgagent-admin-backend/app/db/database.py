from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from .models import Base
from app.config.settings import settings

# 使用与 mgagent-backend 相同的数据库文件，实现数据共享
DB_PATH = Path(__file__).parent.parent.parent.parent / "mgagent-backend" / "data" / "chat.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session(db: Session = None):
    if db:
        return db
    return next(get_db())
