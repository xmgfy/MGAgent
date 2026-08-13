"""
统一配置模块 - Admin Backend

唯一技术栈: MySQL + Milvus + MinIO
大模型相关配置统一从数据库中读取，不再使用本地静态配置。
"""
from pydantic_settings import BaseSettings
from pathlib import Path
import os
import secrets


class Settings(BaseSettings):
    """统一配置"""
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
    
    ADMIN_API_HOST: str = "0.0.0.0"
    ADMIN_API_PORT: int = 8001
    DEBUG: bool = True
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "mgagent"
    MYSQL_PASSWORD: str = "mgagent_password_2024"
    MYSQL_DATABASE: str = "mgagent"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "mgagent_knowledge"
    
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "mgagent-documents"
    
    DOCUMENT_DIR: str = "../mgagent-backend/data/documents"

settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BASE_DIR.parent
MGAGENT_BACKEND_DIR = PROJECT_DIR / "mgagent-backend"


def get_database_url() -> str:
    return f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}?charset=utf8mb4"


def get_document_dir() -> Path:
    return (BASE_DIR / settings.DOCUMENT_DIR).resolve()


def get_minio_config() -> dict:
    return {
        "host": settings.MINIO_HOST,
        "port": settings.MINIO_PORT,
        "access_key": settings.MINIO_ACCESS_KEY,
        "secret_key": settings.MINIO_SECRET_KEY,
        "bucket": settings.MINIO_BUCKET,
    }


DOCUMENT_DIR = get_document_dir()
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)


def get_scheme_info() -> dict:
    """获取当前技术栈信息（健康检查/状态接口返回）"""
    return {
        "scheme": "mysql",
        "name": "MySQL + Milvus + MinIO",
        "description": "高性能生产级部署",
        "database": {
            "type": "mysql",
            "name": "MySQL",
            "version": "8.0",
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "database": settings.MYSQL_DATABASE,
        },
        "vector_database": {
            "type": "milvus",
            "name": "Milvus",
            "version": "2.4",
            "host": settings.MILVUS_HOST,
            "port": settings.MILVUS_PORT,
            "collection": settings.MILVUS_COLLECTION,
        },
        "file_storage": {
            "type": "minio",
            "name": "MinIO",
            "host": settings.MINIO_HOST,
            "port": settings.MINIO_PORT,
            "bucket": settings.MINIO_BUCKET,
        },
    }
