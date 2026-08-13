from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
    
    DOCUMENT_DIR: str = "data/documents"
    
    DATABASE_URL: str = "mysql+pymysql://mgagent:mgagent_password_2024@localhost:3306/mgagent?charset=utf8mb4"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "mgagent_knowledge"
    
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

for dir_path in [DATA_DIR, DOCUMENT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def get_active_model_config_row(model_type: str = "chat", tenant_id: str | None = None, scenario: str | None = None):
    """获取 ORM 行 — 多租户+多场景优先级"""
    from app.services.model_config_service import get_active_model_config_row as _get
    return _get(model_type=model_type, tenant_id=tenant_id, scenario=scenario)


def get_active_model_config(model_type: str = "chat", tenant_id: str | None = None, scenario: str | None = None) -> dict:
    """获取 dict — 兼容旧调用方"""
    from app.services.model_config_service import get_active_model_config_dict
    return get_active_model_config_dict(model_type=model_type, tenant_id=tenant_id, scenario=scenario)


def get_embedding_model_config():
    from app.services.model_config_service import get_embedding_model_config
    return get_embedding_model_config()
