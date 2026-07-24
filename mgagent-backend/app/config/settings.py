from pydantic_settings import BaseSettings
from pathlib import Path
import requests

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    CHROMA_PERSIST_DIR: str = "data/chroma"
    DOCUMENT_DIR: str = "data/documents"
    
    DATABASE_URL: str = "sqlite:///./data/chat.db"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    ADMIN_API_URL: str = "http://localhost:8001/admin/api"
    
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENT_DIR = DATA_DIR / "documents"
CHROMA_DIR = DATA_DIR / "chroma"

for dir_path in [DATA_DIR, DOCUMENT_DIR, CHROMA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

def get_active_model_config():
    """从admin-backend获取当前启用的模型配置"""
    try:
        response = requests.get(f"{settings.ADMIN_API_URL}/model/config/public", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    return None