from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    DOCUMENT_DIR: str = "../mgagent-backend/data/documents"
    
    # MySQL 数据库配置 - 与 mgagent-backend 共享同一数据库
    DATABASE_URL: str = "mysql+pymysql://mgagent:mgagent_password_2024@localhost:3306/mgagent?charset=utf8mb4"
    
    # Milvus 向量数据库配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "mgagent_knowledge"
    
    ADMIN_API_HOST: str = "0.0.0.0"
    ADMIN_API_PORT: int = 8001
    
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR.parent / "mgagent-backend" / "data"
DOCUMENT_DIR = DATA_DIR / "documents"

for dir_path in [DOCUMENT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)