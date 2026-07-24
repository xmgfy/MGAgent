from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.models import Base
from app.config.settings import settings
from sqlalchemy import create_engine
import uvicorn

Base.metadata.create_all(bind=create_engine(settings.DATABASE_URL))

app = FastAPI(
    title="MGAgent 智能客服助手",
    description="基于LangChain + FastAPI + RAG + MCP的智能体系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "MGAgent 智能客服助手 API",
        "endpoints": {
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "sessions": "/api/sessions",
            "documents": "/api/documents",
            "tools": "/api/tools",
            "health": "/api/health"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )