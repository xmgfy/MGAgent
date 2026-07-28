"""
统一配置模块 - 支持双技术栈方案
方案1: SQLite + ChromaDB
方案2: MySQL + Milvus

注意：大模型相关配置（API Key、Base URL、模型名称等）统一从数据库中读取，不再使用本地静态配置。
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from enum import Enum
import os
import secrets

class DatabaseScheme(str, Enum):
    """数据库方案枚举"""
    SQLITE = "sqlite"      # 方案1: SQLite + ChromaDB
    MYSQL = "mysql"        # 方案2: MySQL + Milvus

class Settings(BaseSettings):
    """统一配置"""
    
    # ========== 基础配置 ==========
    DATABASE_SCHEME: str = os.getenv("DATABASE_SCHEME", "sqlite")  # sqlite 或 mysql
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ADMIN_API_URL: str = "http://localhost:8001/admin/api"
    DEBUG: bool = True
    
    # JWT 密钥（自动生成，或通过环境变量配置）
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    
    # ========== 方案1: SQLite + ChromaDB 配置 ==========
    SQLITE_DB_PATH: str = "data/chat.db"
    CHROMA_PERSIST_DIR: str = "data/chroma"
    
    # ========== 方案2: MySQL + Milvus 配置 ==========
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "mgagent"
    MYSQL_PASSWORD: str = "mgagent_password_2024"
    MYSQL_DATABASE: str = "mgagent"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "mgagent_knowledge"
    
    # ========== 公共配置 ==========
    DOCUMENT_DIR: str = "data/documents"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# ========== 路径配置 ==========
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENT_DIR = DATA_DIR / "documents"

# ========== 根据方案生成配置 ==========
def get_database_scheme() -> DatabaseScheme:
    """获取当前数据库方案"""
    try:
        return DatabaseScheme(settings.DATABASE_SCHEME)
    except ValueError:
        return DatabaseScheme.SQLITE

def is_sqlite_scheme() -> bool:
    """是否为 SQLite 方案"""
    return get_database_scheme() == DatabaseScheme.SQLITE

def is_mysql_scheme() -> bool:
    """是否为 MySQL 方案"""
    return get_database_scheme() == DatabaseScheme.MYSQL

def get_database_url() -> str:
    """获取数据库连接URL"""
    if is_mysql_scheme():
        return f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}?charset=utf8mb4"
    else:
        sqlite_path = BASE_DIR / settings.SQLITE_DB_PATH
        return f"sqlite:///{sqlite_path}"

def get_chroma_dir() -> Path:
    """获取 ChromaDB 持久化目录"""
    return BASE_DIR / settings.CHROMA_PERSIST_DIR

def get_sqlite_path() -> Path:
    """获取 SQLite 数据库路径"""
    return BASE_DIR / settings.SQLITE_DB_PATH

def get_document_dir() -> Path:
    """获取文档目录"""
    return DOCUMENT_DIR

# ========== 初始化目录 ==========
CHROMA_DIR = get_chroma_dir()
SQLITE_PATH = get_sqlite_path()

for dir_path in [DATA_DIR, DOCUMENT_DIR, CHROMA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ========== 方案信息（供API返回） ==========
def get_scheme_info() -> dict:
    """获取当前方案信息"""
    scheme = get_database_scheme()
    
    if scheme == DatabaseScheme.SQLITE:
        return {
            "scheme": "sqlite",
            "name": "SQLite + ChromaDB",
            "description": "轻量级单机部署，适合开发调试",
            "database": {
                "type": "sqlite",
                "name": "SQLite",
                "version": "3",
                "path": str(SQLITE_PATH),
                "size": _get_file_size(SQLITE_PATH)
            },
            "vector_database": {
                "type": "chromadb",
                "name": "ChromaDB",
                "version": "0.5+",
                "path": str(CHROMA_DIR),
                "collection": "default"
            }
        }
    else:
        return {
            "scheme": "mysql",
            "name": "MySQL + Milvus",
            "description": "高性能生产级部署，适合大规模数据",
            "database": {
                "type": "mysql",
                "name": "MySQL",
                "version": "8.0",
                "host": settings.MYSQL_HOST,
                "port": settings.MYSQL_PORT,
                "database": settings.MYSQL_DATABASE
            },
            "vector_database": {
                "type": "milvus",
                "name": "Milvus",
                "version": "2.4",
                "host": settings.MILVUS_HOST,
                "port": settings.MILVUS_PORT,
                "collection": settings.MILVUS_COLLECTION
            }
        }

def _get_file_size(path: Path) -> int:
    """获取文件大小"""
    try:
        if path.exists():
            return path.stat().st_size
        return 0
    except:
        return 0
