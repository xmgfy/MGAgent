from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.crud.model import (
    create_model_config, get_model_configs, get_model_config_by_id,
    update_model_config, set_active_model, delete_model_config, deactivate_model
)
from app.db.models import Admin, ModelConfig
from .auth import get_current_admin

router = APIRouter()

class ModelConfigRequest(BaseModel):
    name: str
    api_key: str
    api_base: str
    model_name: str

class ModelConfigUpdateRequest(BaseModel):
    api_key: str = None
    api_base: str = None
    model_name: str = None

class ModelConfigResponse(BaseModel):
    id: str
    name: str
    api_key_masked: str
    api_base: str
    model_name: str
    is_active: bool
    created_at: str
    updated_at: str

@router.post("/model/config")
async def create_model_config_endpoint(
    request: ModelConfigRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(ModelConfig).filter(ModelConfig.name == request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="模型配置名称已存在")
    
    config = create_model_config(db, request.name, request.api_key, request.api_base, request.model_name)
    
    return {
        "id": config.id,
        "name": config.name,
        "api_key_masked": config.api_key[:4] + "****" + config.api_key[-4:],
        "api_base": config.api_base,
        "model_name": config.model_name,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }

@router.get("/model/config", response_model=ModelConfigResponse)
async def get_active_model_config(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    configs = get_model_configs(db, is_active=True)
    if not configs:
        raise HTTPException(status_code=404, detail="未配置任何模型")
    
    config = configs[0]
    return {
        "id": config.id,
        "name": config.name,
        "api_key_masked": config.api_key[:4] + "****" + config.api_key[-4:],
        "api_base": config.api_base,
        "model_name": config.model_name,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }

@router.get("/model/config/public")
async def get_public_model_config(db: Session = Depends(get_db)):
    """供外部服务访问的模型配置接口（无需认证），无配置时抛出异常"""
    configs = get_model_configs(db, is_active=True)
    if not configs:
        raise HTTPException(status_code=404, detail="未配置任何模型，请在admin管理端配置并启用模型")
    
    config = configs[0]
    return {
        "id": config.id,
        "name": config.name,
        "api_key": config.api_key,
        "api_base": config.api_base,
        "model_name": config.model_name,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }

@router.get("/model/configs", response_model=List[ModelConfigResponse])
async def get_model_configs_endpoint(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    configs = get_model_configs(db)
    
    return [{
        "id": c.id,
        "name": c.name,
        "api_key_masked": c.api_key[:4] + "****" + c.api_key[-4:],
        "api_base": c.api_base,
        "model_name": c.model_name,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat()
    } for c in configs]

@router.put("/model/config/{config_id}")
async def update_model_config_endpoint(
    config_id: str,
    request: ModelConfigUpdateRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = get_model_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    update_data = {}
    if request.api_key is not None:
        update_data["api_key"] = request.api_key
    if request.api_base is not None:
        update_data["api_base"] = request.api_base
    if request.model_name is not None:
        update_data["model_name"] = request.model_name
    
    updated_config = update_model_config(db, config_id, **update_data)
    
    return {
        "id": updated_config.id,
        "name": updated_config.name,
        "api_key_masked": updated_config.api_key[:4] + "****" + updated_config.api_key[-4:],
        "api_base": updated_config.api_base,
        "model_name": updated_config.model_name,
        "is_active": updated_config.is_active,
        "created_at": updated_config.created_at.isoformat(),
        "updated_at": updated_config.updated_at.isoformat()
    }

@router.post("/model/config/{config_id}/activate")
async def activate_model_config_endpoint(
    config_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = get_model_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    activated_config = set_active_model(db, config_id)
    
    return {
        "id": activated_config.id,
        "name": activated_config.name,
        "api_key_masked": activated_config.api_key[:4] + "****" + activated_config.api_key[-4:],
        "api_base": activated_config.api_base,
        "model_name": activated_config.model_name,
        "is_active": activated_config.is_active,
        "created_at": activated_config.created_at.isoformat(),
        "updated_at": activated_config.updated_at.isoformat()
    }

@router.post("/model/config/{config_id}/deactivate")
async def deactivate_model_config_endpoint(
    config_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = get_model_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    if not config.is_active:
        raise HTTPException(status_code=400, detail="模型配置未启用")
    
    deactivated_config = deactivate_model(db, config_id)
    
    return {
        "id": deactivated_config.id,
        "name": deactivated_config.name,
        "api_key_masked": deactivated_config.api_key[:4] + "****" + deactivated_config.api_key[-4:],
        "api_base": deactivated_config.api_base,
        "model_name": deactivated_config.model_name,
        "is_active": deactivated_config.is_active,
        "created_at": deactivated_config.created_at.isoformat(),
        "updated_at": deactivated_config.updated_at.isoformat()
    }

@router.delete("/model/config/{config_id}")
async def delete_model_config_endpoint(
    config_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = get_model_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    if config.is_active:
        raise HTTPException(status_code=400, detail="无法删除正在使用的模型配置")
    
    if delete_model_config(db, config_id):
        return {"message": "模型配置已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")

@router.get("/model/test")
async def test_model_connection(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    configs = get_model_configs(db, is_active=True)
    if not configs:
        return {"status": "failed", "error": "未配置任何模型"}
    
    config = configs[0]
    
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=config.model_name,
            api_key=config.api_key,
            base_url=config.api_base,
            temperature=0.1
        )
        
        response = llm.invoke("Hello, this is a test.")
        
        return {"status": "success", "response": response.content[:50]}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
