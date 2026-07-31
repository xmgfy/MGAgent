"""
应用入口 - 注册路由和中间件
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.db.database import init_db
from app.config.config import settings, get_scheme_info, get_database_scheme
from app.exceptions import BusinessException
from app.core.logger import logger
import uvicorn

# 初始化数据库
init_db()

app = FastAPI(
    title="MGAgent 智能客服助手",
    description="基于LangChain + FastAPI + RAG + MCP的智能体系统",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册全局异常处理器
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """业务异常处理器"""
    logger.warning(f"业务异常: {exc.message}, path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理异常: {str(exc)}, path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试",
        }
    )

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    scheme = get_database_scheme()
    return {
        "message": "MGAgent 智能客服助手 API",
        "version": "2.0.0",
        "database_scheme": scheme.value,
        "endpoints": {
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "sessions": "/api/sessions",
            "documents": "/api/documents",
            "tools": "/api/tools",
            "health": "/api/health",
            "scheme": "/api/scheme"
        }
    }

@app.get("/api/scheme")
async def get_current_scheme():
    """获取当前数据库方案信息"""
    return get_scheme_info()

@app.get("/api/health")
async def health_check():
    """健康检查"""
    scheme_info = get_scheme_info()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database_scheme": scheme_info["scheme"],
        "database_type": scheme_info["database"]["type"],
        "vector_db_type": scheme_info["vector_database"]["type"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
