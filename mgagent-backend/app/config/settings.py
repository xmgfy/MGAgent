from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
    
    CHROMA_PERSIST_DIR: str = "data/chroma"
    DOCUMENT_DIR: str = "data/documents"
    
    # MySQL 数据库配置
    DATABASE_URL: str = "mysql+pymysql://mgagent:mgagent_password_2024@localhost:3306/mgagent?charset=utf8mb4"
    
    # Milvus 向量数据库配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "mgagent_knowledge"
    
    # MinIO 对象存储配置（MySQL 模式使用）
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "mgagent-documents"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    ADMIN_API_URL: str = "http://localhost:8001/admin/api"
    
    DEBUG: bool = True

settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENT_DIR = DATA_DIR / "documents"
CHROMA_DIR = DATA_DIR / "chroma"

for dir_path in [DATA_DIR, DOCUMENT_DIR, CHROMA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def get_active_model_config():
    """从数据库获取当前启用的模型配置，无配置时抛出异常"""
    from app.services.model_config_service import get_active_model_config as get_config
    return get_config()
