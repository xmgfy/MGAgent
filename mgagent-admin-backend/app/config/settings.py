from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    CHROMA_PERSIST_DIR: str = "../mgagent-backend/data/chroma"
    DOCUMENT_DIR: str = "../mgagent-backend/data/documents"
    
    DATABASE_URL: str = "sqlite:///../mgagent-backend/data/chat.db"
    
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
CHROMA_DIR = DATA_DIR / "chroma"

for dir_path in [DATA_DIR, DOCUMENT_DIR, CHROMA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)