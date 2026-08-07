from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import requests
import logging
import json
import uuid

from app.db.database import get_db
from app.db.crud.model import (
    create_model_config, get_model_configs, get_model_config_by_id,
    update_model_config, set_active_model, delete_model_config, deactivate_model
)
from app.db.models import Admin, ModelConfig, Provider as ProviderORM
from app.config.local_models import get_local_models_list
from app.config.providers import (
    seed_providers, provider_orm_to_dict, get_provider_by_code,
    classify_model_type, get_known_dimension
)
from .auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter()


class ModelConfigRequest(BaseModel):
    name: str
    model_name: str
    model_type: str = "chat"
    provider: str = "openai"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    dimension: Optional[int] = None
    is_local: bool = False
    scenario: Optional[str] = None
    tenant_id: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None


class ModelConfigUpdateRequest(BaseModel):
    name: Optional[str] = None
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    dimension: Optional[int] = None
    is_local: Optional[bool] = None
    scenario: Optional[str] = None
    tenant_id: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None


class DiscoverModelsRequest(BaseModel):
    provider_code: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model_type: Optional[str] = None


class ProviderCreateRequest(BaseModel):
    code: str
    display_name: str
    favicon_domain: Optional[str] = None
    default_api_base: Optional[str] = ""
    supports_api_key: bool = True
    supports_local: bool = False
    supports_discover: bool = True
    supported_model_types: List[str] = ["chat"]
    fallback_models: Optional[Dict[str, List[str]]] = None
    description: Optional[str] = None
    api_key: Optional[str] = None


class ProviderUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    favicon_domain: Optional[str] = None
    default_api_base: Optional[str] = None
    supports_api_key: Optional[bool] = None
    supports_local: Optional[bool] = None
    supports_discover: Optional[bool] = None
    supported_model_types: Optional[List[str]] = None
    fallback_models: Optional[Dict[str, List[str]]] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None


def _mask_api_key(api_key: Optional[str]) -> str:
    """脱敏 API Key"""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return api_key[:4] + "****" + api_key[-4:]


def _config_to_response(config: ModelConfig, include_full_key: bool = False) -> dict:
    """
    将 ModelConfig 转为响应字典
    
    Args:
        config: ModelConfig 数据库对象
        include_full_key: 是否返回完整 API Key（仅内部调用场景为 True）
    """
    api_key = config.api_key or ""
    return {
        "id": config.id,
        "name": config.name,
        "model_type": config.model_type,
        "provider": config.provider,
        "api_key": api_key if include_full_key else "",
        "api_key_masked": _mask_api_key(api_key),
        "api_base": config.api_base or "",
        "model_name": config.model_name,
        "dimension": config.dimension,
        "is_local": config.is_local or False,
        "is_active": config.is_active,
        "scenario": config.scenario,
        "tenant_id": config.tenant_id,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_tokens": config.max_tokens,
        "presence_penalty": config.presence_penalty,
        "frequency_penalty": config.frequency_penalty,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat()
    }


def _get_provider_from_db(db: Session, code: str, include_full_key: bool = False) -> Optional[Dict[str, Any]]:
    row = db.query(ProviderORM).filter(ProviderORM.code == code).first()
    if row:
        result = provider_orm_to_dict(row)
        if include_full_key:
            result["api_key"] = row.api_key or ""
        return result
    p = get_provider_by_code(code)
    if p:
        return {**p, "id": None, "api_key": "", "api_key_masked": "", "is_system": True, "is_active": True}
    return None


@router.get("/model/providers")
async def list_providers(
    model_type: Optional[str] = Query(None, description="按模型类型过滤: chat, embedding"),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(ProviderORM)
    rows = query.all()
    # admin 登录态，创建模型时需预填 Provider 级 API Key → 返回明文
    result = [provider_orm_to_dict(r, include_full_key=True) for r in rows]
    if model_type:
        result = [p for p in result if model_type in p["supported_model_types"]]
    return result


def _discover_via_openai_compatible(api_base: str, api_key: str, model_type_filter: Optional[str]) -> List[Dict[str, Any]]:
    """通过 OpenAI 兼容的 /v1/models 接口动态发现模型"""
    if not api_base.endswith("/v1"):
        api_base = api_base.rstrip("/") + "/v1"
    url = f"{api_base}/models"

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    models_raw = data.get("data", [])
    results: List[Dict[str, Any]] = []
    seen: set = set()

    for item in models_raw:
        model_id = item.get("id", "")
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)

        classified = classify_model_type(model_id)
        if classified is None:
            continue
        if model_type_filter and classified != model_type_filter:
            continue

        results.append({
            "model_id": model_id,
            "model_type": classified,
            "dimension": get_known_dimension(model_id),
            "owned_by": item.get("owned_by", ""),
        })

    results.sort(key=lambda x: (x["model_type"], x["model_id"]))
    return results


def _discover_via_ollama(api_base: str, model_type_filter: Optional[str]) -> List[Dict[str, Any]]:
    """通过 Ollama /api/tags 接口发现本地已下载模型"""
    clean_base = api_base.replace("/v1", "").rstrip("/")
    url = f"{clean_base}/api/tags"

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    models_raw = data.get("models", [])
    results: List[Dict[str, Any]] = []

    for item in models_raw:
        model_name = item.get("name", "")
        if not model_name:
            continue

        base_name = model_name.split(":")[0] if ":" in model_name else model_name
        classified = classify_model_type(base_name)
        if classified is None:
            continue
        if model_type_filter and classified != model_type_filter:
            continue

        results.append({
            "model_id": model_name,
            "model_type": classified,
            "dimension": get_known_dimension(base_name),
            "size_mb": item.get("size", 0) // (1024 * 1024) if item.get("size") else None,
            "modified_at": item.get("modified_at", ""),
        })

    results.sort(key=lambda x: (x["model_type"], x["model_id"]))
    return results


@router.post("/model/providers/discover-models")
async def discover_provider_models(
    request: DiscoverModelsRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    动态发现指定 Provider 账号下可用的模型列表

    安全说明：api_key 仅在本次请求内存中使用，不记录、不缓存、不持久化
    """
    provider = _get_provider_from_db(db, request.provider_code, include_full_key=True)
    if not provider:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {request.provider_code}")

    if not provider.get("supports_discover", False):
        raise HTTPException(
            status_code=400,
            detail=f"提供商 {provider['display_name']} 不支持动态发现模型，请手动输入"
        )

    api_base = request.api_base or provider.get("default_api_base", "")
    api_key = request.api_key or provider.get("api_key") or ""

    try:
        if request.provider_code == "ollama":
            models = _discover_via_ollama(api_base, request.model_type)
        else:
            if provider["supports_api_key"] and not api_key:
                raise HTTPException(status_code=400, detail=f"提供商 {provider['display_name']} 需要 API Key 才能发现模型")
            models = _discover_via_openai_compatible(api_base, api_key, request.model_type)

        chat_count = sum(1 for m in models if m["model_type"] == "chat")
        emb_count = sum(1 for m in models if m["model_type"] == "embedding")
        rerank_count = sum(1 for m in models if m["model_type"] == "reranker")

        return {
            "provider": provider["code"],
            "provider_name": provider["display_name"],
            "total": len(models),
            "chat_count": chat_count,
            "embedding_count": emb_count,
            "reranker_count": rerank_count,
            "models": models,
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="连接提供商超时，请检查 API Base 地址")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="无法连接到提供商服务，请检查 API Base 地址和网络")
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else 500
        detail = "API Key 无效或权限不足" if status == 401 else f"提供商返回错误: {status}"
        raise HTTPException(status_code=status, detail=detail)
    except Exception as e:
        logger.error("Discover models failed: provider=%s error=%s", request.provider_code, str(e))
        raise HTTPException(status_code=500, detail=f"发现模型失败: {str(e)}")


@router.get("/model/list")
async def get_user_model_list(
    model_type: Optional[str] = Query(None, description="按模型类型过滤: chat, embedding"),
    only_active: bool = Query(True, description="是否只返回已启用的模型"),
    db: Session = Depends(get_db)
):
    """
    面向用户/对话侧的可用模型列表接口（无需管理员认证）
    可被 mgagent-backend 或前端调用
    """
    query = db.query(ModelConfig)
    
    if only_active:
        query = query.filter(ModelConfig.is_active == True)
    
    if model_type:
        query = query.filter(ModelConfig.model_type == model_type)
    
    configs = query.all()
    
    result = []
    for config in configs:
        result.append({
            "id": config.id,
            "name": config.name,
            "model_type": config.model_type,
            "provider": config.provider,
            "model_name": config.model_name,
            "dimension": config.dimension,
            "is_local": config.is_local or False,
            "is_active": config.is_active,
        })
    
    return result


@router.post("/model/config")
async def create_model_config_endpoint(
    request: ModelConfigRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(ModelConfig).filter(ModelConfig.name == request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="模型配置名称已存在")
    
    provider = _get_provider_from_db(db, request.provider)
    if not provider:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {request.provider}")
    
    if request.model_type not in provider["supported_model_types"]:
        raise HTTPException(
            status_code=400,
            detail=f"该提供商不支持 {request.model_type} 类型，仅支持: {provider['supported_model_types']}"
        )
    
    if provider["supports_api_key"] and not request.is_local:
        if not request.api_key:
            raise HTTPException(status_code=400, detail=f"提供商 {provider['display_name']} 需要 API Key")
    
    api_base = request.api_base or provider.get("default_api_base", "")
    
    config = create_model_config(
        db,
        name=request.name,
        model_name=request.model_name,
        model_type=request.model_type,
        provider=request.provider,
        api_key=request.api_key,
        api_base=api_base,
        dimension=request.dimension,
        is_local=request.is_local,
        scenario=request.scenario,
        tenant_id=request.tenant_id,
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens,
        presence_penalty=request.presence_penalty,
        frequency_penalty=request.frequency_penalty,
    )
    
    return _config_to_response(config, include_full_key=False)


@router.get("/model/config")
async def get_active_model_config(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    configs = get_model_configs(db, is_active=True)
    if not configs:
        raise HTTPException(status_code=404, detail="未配置任何模型")
    
    config = configs[0]
    return _config_to_response(config, include_full_key=False)


@router.get("/model/config/public")
async def get_public_model_config(db: Session = Depends(get_db)):
    """
    供外部服务访问的模型配置接口（无需认证）
    
    安全说明：
    - 不返回 api_key 和 api_base，仅返回模型标识信息
    - mgagent-backend 应直接从共享数据库读取完整配置
    """
    configs = get_model_configs(db, is_active=True)
    if not configs:
        raise HTTPException(status_code=404, detail="未配置任何模型，请在admin管理端配置并启用模型")
    
    result = []
    for config in configs:
        result.append({
            "id": config.id,
            "name": config.name,
            "model_type": config.model_type,
            "provider": config.provider,
            "model_name": config.model_name,
            "dimension": config.dimension,
            "is_local": config.is_local or False,
            "is_active": config.is_active,
        })
    
    return result


@router.get("/model/configs")
async def get_model_configs_endpoint(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    configs = get_model_configs(db)
    return [_config_to_response(c, include_full_key=False) for c in configs]


@router.get("/model/config/{config_id}")
async def get_model_config_detail(
    config_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取单个模型配置详情（编辑时使用，不返回完整 API Key）"""
    config = get_model_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return _config_to_response(config, include_full_key=False)


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
    if request.name is not None:
        update_data["name"] = request.name
    if request.model_name is not None:
        update_data["model_name"] = request.model_name
    if request.model_type is not None:
        update_data["model_type"] = request.model_type
    if request.provider is not None:
        provider = _get_provider_from_db(db, request.provider)
        if provider is None:
            raise HTTPException(status_code=400, detail=f"不支持的提供商: {request.provider}")
        update_data["provider"] = request.provider
        if not request.api_base:
            update_data["api_base"] = provider.get("default_api_base", "")
    if request.api_key is not None:
        update_data["api_key"] = request.api_key
    if request.api_base is not None:
        update_data["api_base"] = request.api_base
    if request.dimension is not None:
        update_data["dimension"] = request.dimension
    if request.is_local is not None:
        update_data["is_local"] = request.is_local
    if request.scenario is not None:
        update_data["scenario"] = request.scenario
    if request.tenant_id is not None:
        update_data["tenant_id"] = request.tenant_id
    if request.temperature is not None:
        update_data["temperature"] = request.temperature
    if request.top_p is not None:
        update_data["top_p"] = request.top_p
    if request.max_tokens is not None:
        update_data["max_tokens"] = request.max_tokens
    if request.presence_penalty is not None:
        update_data["presence_penalty"] = request.presence_penalty
    if request.frequency_penalty is not None:
        update_data["frequency_penalty"] = request.frequency_penalty
    
    updated_config = update_model_config(db, config_id, **update_data)
    
    return _config_to_response(updated_config, include_full_key=False)


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
    
    return _config_to_response(activated_config, include_full_key=False)


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
    
    return _config_to_response(deactivated_config, include_full_key=False)


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


@router.get("/model/local-models")
async def get_local_embedding_models(
    admin: Admin = Depends(get_current_admin)
):
    """获取可用的本地 Embedding 模型列表（预设）"""
    return get_local_models_list()


@router.post("/model/local-models/download")
async def download_local_model(
    request: dict,
    admin: Admin = Depends(get_current_admin)
):
    """下载本地模型（部署时使用，支持长任务）"""
    import os
    from app.config.local_models import get_model_by_id
    
    model_id = request.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="缺少 model_id 参数")
    
    model_info = get_model_by_id(model_id)
    if not model_info:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    os.environ["HF_ENDPOINT"] = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
    
    try:
        from sentence_transformers import SentenceTransformer
        cache_dir = os.path.expanduser("~/.cache/huggingface")
        os.makedirs(cache_dir, exist_ok=True)
        
        model = SentenceTransformer(model_info["name"], cache_folder=cache_dir)
        
        return {
            "status": "success",
            "model_id": model_id,
            "model_name": model_info["name"],
            "dimension": model_info["dimension"],
            "message": f"模型 {model_info['display_name']} 下载成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/model/test")
async def test_model_connection(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    测试当前活跃模型的连接（仅用于管理员验证，内部调用）
    
    说明：此接口在服务端内部使用完整 api_key，但不返回给客户端
    """
    configs = get_model_configs(db, is_active=True)
    if not configs:
        return {"status": "failed", "error": "未配置任何模型"}
    
    config = configs[0]
    
    try:
        provider = config.provider
        
        if provider == "local" or config.is_local:
            return {"status": "success", "response": "本地模型配置正确（将在索引时自动加载）"}
        
        if provider == "ollama":
            import requests
            ollama_base = config.api_base or "http://localhost:11434/v1"
            try:
                resp = requests.get(ollama_base.replace("/v1", ""), timeout=5)
                if resp.status_code == 200:
                    return {"status": "success", "response": "Ollama 服务运行正常"}
                else:
                    return {"status": "failed", "error": f"Ollama 响应异常: {resp.status_code}"}
            except Exception as e:
                return {"status": "failed", "error": f"无法连接 Ollama: {str(e)}"}
        
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


@router.post("/model/providers")
async def create_provider(
    request: ProviderCreateRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(ProviderORM).filter(ProviderORM.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Provider code '{request.code}' 已存在")

    if not request.supported_model_types:
        raise HTTPException(status_code=400, detail="supported_model_types 不能为空")

    new_row = ProviderORM(
        id=str(uuid.uuid4()),
        code=request.code,
        display_name=request.display_name,
        favicon_domain=request.favicon_domain or "",
        default_api_base=request.default_api_base or "",
        supports_api_key=request.supports_api_key,
        supports_local=request.supports_local,
        supports_discover=request.supports_discover,
        supported_model_types=json.dumps(request.supported_model_types),
        fallback_models=json.dumps(request.fallback_models or {}),
        description=request.description or "",
        api_key=request.api_key or "",
        is_system=False,
        is_active=True,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return provider_orm_to_dict(new_row)


@router.put("/model/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    request: ProviderUpdateRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    row = db.query(ProviderORM).filter(ProviderORM.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider 不存在")

    if request.display_name is not None:
        row.display_name = request.display_name
    if request.favicon_domain is not None:
        row.favicon_domain = request.favicon_domain
    if request.default_api_base is not None:
        row.default_api_base = request.default_api_base
    if request.supports_api_key is not None:
        row.supports_api_key = request.supports_api_key
    if request.supports_local is not None:
        row.supports_local = request.supports_local
    if request.supports_discover is not None:
        row.supports_discover = request.supports_discover
    if request.supported_model_types is not None:
        if not request.supported_model_types:
            raise HTTPException(status_code=400, detail="supported_model_types 不能为空")
        row.supported_model_types = json.dumps(request.supported_model_types)
    if request.fallback_models is not None:
        row.fallback_models = json.dumps(request.fallback_models)
    if request.description is not None:
        row.description = request.description
    if request.api_key is not None:
        row.api_key = request.api_key
    if request.is_active is not None:
        row.is_active = request.is_active

    db.commit()
    db.refresh(row)
    return provider_orm_to_dict(row)


@router.delete("/model/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    row = db.query(ProviderORM).filter(ProviderORM.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider 不存在")

    if row.is_system:
        raise HTTPException(status_code=400, detail="系统内置 Provider 不可删除")

    db.delete(row)
    db.commit()
    return {"message": "Provider 已删除"}


@router.post("/model/providers/{provider_id}/toggle")
async def toggle_provider_active(
    provider_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    row = db.query(ProviderORM).filter(ProviderORM.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider 不存在")

    row.is_active = not bool(row.is_active)
    db.commit()
    db.refresh(row)
    return provider_orm_to_dict(row)
