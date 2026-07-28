from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.admins import router as admins_router
from app.api.tenants import router as tenants_router
from app.api.model import router as model_router
from app.api.system import router as system_router
from app.api.storage import router as storage_router
from app.api.knowledge import router as knowledge_router
from app.api.vector import router as vector_router
from app.api.dashboard import router as dashboard_router
from app.config.config import settings, get_scheme_info, get_database_scheme
from app.db import init_db
from app.db.database import get_db, SessionLocal
from app.db.crud.admin import create_admin, get_admin_by_username
import uvicorn

app = FastAPI(
    title="MGAgent 管理台",
    description="MGAgent 智能体系统管理后台 API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/admin/api")
app.include_router(users_router, prefix="/admin/api")
app.include_router(admins_router, prefix="/admin/api")
app.include_router(tenants_router, prefix="/admin/api")
app.include_router(model_router, prefix="/admin/api")
app.include_router(system_router, prefix="/admin/api")
app.include_router(storage_router, prefix="/admin/api")
app.include_router(knowledge_router, prefix="/admin/api")
app.include_router(vector_router, prefix="/admin/api")
app.include_router(dashboard_router, prefix="/admin/api")

@app.on_event("startup")
async def startup_event():
    init_db()
    
    db = next(get_db())
    if not get_admin_by_username(db, "admin"):
        create_admin(
            db,
            username="admin",
            email="admin@mgagent.com",
            password="admin123",
            role="platform_admin",
            tenant_id=None
        )
    db.close()

@app.get("/")
async def root():
    scheme = get_database_scheme()
    return {
        "message": "MGAgent 管理台 API",
        "version": "2.0.0",
        "database_scheme": scheme.value,
        "endpoints": {
            "auth": "/admin/api/auth",
            "users": "/admin/api/users",
            "tenants": "/admin/api/tenants",
            "model": "/admin/api/model",
            "system": "/admin/api/system",
            "storage_db": "/admin/api/storage-db",
            "knowledge_base": "/admin/api/knowledge-base",
            "vector_db": "/admin/api/vector-db",
            "dashboard": "/admin/api/dashboard",
            "health": "/admin/api/health",
            "scheme": "/admin/api/scheme"
        }
    }

@app.get("/admin/api/scheme")
async def get_current_scheme():
    """获取当前数据库方案信息"""
    return get_scheme_info()

@app.get("/admin/api/health")
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
        host=settings.ADMIN_API_HOST,
        port=settings.ADMIN_API_PORT,
        reload=settings.DEBUG
    )
