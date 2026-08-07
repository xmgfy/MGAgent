"""
模型配置服务 - Admin Backend
从数据库读取模型配置，支持 chat 和 embedding 两种类型
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.db.models import ModelConfig
from app.db.database import get_session
import uuid


def get_active_model_config(db: Session = None, model_type: str = "chat") -> Dict[str, Any]:
    """获取当前活跃的模型配置，按 model_type 分组"""
    if db is None:
        db = get_session()

    try:
        config = db.query(ModelConfig).filter(
            ModelConfig.is_active == True,
            ModelConfig.model_type == model_type
        ).first()
        if not config:
            type_label = "对话模型" if model_type == "chat" else "Embedding模型"
            raise ValueError(f"未配置活跃的{type_label}，请在模型管理中配置并启用")

        return _config_to_dict(config)
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"获取模型配置失败: {e}")


def get_active_embedding_config(db: Session = None) -> Optional[Dict[str, Any]]:
    """获取当前活跃的 Embedding 模型配置"""
    if db is None:
        db = get_session()

    try:
        config = db.query(ModelConfig).filter(
            ModelConfig.is_active == True,
            ModelConfig.model_type == "embedding"
        ).first()
        if not config:
            return None
        return _config_to_dict(config)
    except Exception as e:
        raise Exception(f"获取 Embedding 配置失败: {e}")


def _config_to_dict(config: ModelConfig) -> Dict[str, Any]:
    """将 ModelConfig 转为字典"""
    return {
        "id": config.id,
        "name": config.name,
        "model_type": config.model_type,
        "provider": config.provider,
        "api_key": config.api_key,
        "api_base": config.api_base,
        "model_name": config.model_name,
        "dimension": config.dimension,
        "is_local": config.is_local,
        "is_active": config.is_active
    }


def create_embeddings_model(config: Dict[str, Any]):
    """根据配置创建 Embedding 模型实例"""
    provider = config.get("provider", "openai")
    is_local = config.get("is_local", False)
    model_name = config.get("model_name", "")

    if is_local or provider == "local":
        # 本地模型 - 使用 sentence-transformers
        try:
            import os
            # 设置 HuggingFace 镜像源（国内网络必需）
            if not os.environ.get("HF_ENDPOINT"):
                os.environ["HF_ENDPOINT"] = os.environ.get(
                    "HF_ENDPOINT", "https://hf-mirror.com"
                )
            
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        except ImportError:
            raise ImportError(
                "sentence-transformers 未安装，请执行: pip install sentence-transformers"
            )
        except Exception as e:
            raise Exception(f"初始化本地 Embedding 模型失败: {str(e)}")
    else:
        # 云端模型 - 使用 OpenAI 兼容接口
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                api_key=config.get("api_key", ""),
                base_url=config.get("api_base", ""),
                model=model_name
            )
        except ImportError:
            raise ImportError("langchain_openai 未安装，请执行: pip install langchain-openai")
        except Exception as e:
            raise Exception(f"初始化 Embedding 模型失败: {str(e)}")


def get_embeddings_model(db: Session = None):
    """获取当前活跃的 Embedding 模型实例"""
    config = get_active_embedding_config(db)
    if not config:
        raise ValueError(
            "未配置 Embedding 模型，请在模型管理中添加 Embedding 类型的模型并启用"
        )
    return create_embeddings_model(config)


def get_all_model_configs(db: Session = None) -> list:
    """获取所有模型配置"""
    if db is None:
        db = get_session()
    
    try:
        configs = db.query(ModelConfig).all()
        return [_config_to_dict(config) for config in configs]
    except Exception as e:
        raise Exception(f"获取所有模型配置失败: {e}")


def create_model_config(config_data: Dict[str, Any], db: Session = None) -> Dict[str, Any]:
    """创建新的模型配置"""
    if db is None:
        db = get_session()
    
    try:
        config = ModelConfig(
            id=str(uuid.uuid4()),
            name=config_data["name"],
            model_type=config_data.get("model_type", "chat"),
            provider=config_data.get("provider", "openai"),
            api_key=config_data.get("api_key"),
            api_base=config_data.get("api_base"),
            model_name=config_data["model_name"],
            dimension=config_data.get("dimension"),
            is_local=config_data.get("is_local", False),
            is_active=config_data.get("is_active", False)
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        
        return _config_to_dict(config)
    except Exception as e:
        db.rollback()
        raise Exception(f"创建模型配置失败: {str(e)}")


def update_model_config(config_id: str, config_data: Dict[str, Any], db: Session = None) -> Dict[str, Any]:
    """更新模型配置"""
    if db is None:
        db = get_session()
    
    try:
        config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
        if not config:
            raise Exception("模型配置不存在")
        
        for field in ["name", "model_type", "provider", "api_key", "api_base", "model_name", "dimension", "is_local", "is_active"]:
            if field in config_data:
                setattr(config, field, config_data[field])
        
        db.commit()
        db.refresh(config)
        
        return _config_to_dict(config)
    except Exception as e:
        db.rollback()
        raise Exception(f"更新模型配置失败: {str(e)}")


def delete_model_config(config_id: str, db: Session = None) -> bool:
    """删除模型配置"""
    if db is None:
        db = get_session()
    
    try:
        config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
        if not config:
            raise Exception("模型配置不存在")
        
        db.delete(config)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise Exception(f"删除模型配置失败: {str(e)}")


def set_active_model_config(config_id: str, db: Session = None) -> bool:
    """设置活跃的模型配置（同类型互斥）"""
    if db is None:
        db = get_session()
    
    try:
        config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
        if not config:
            raise Exception("模型配置不存在")
        
        # 禁用同类型的其他配置
        db.query(ModelConfig).filter(
            ModelConfig.model_type == config.model_type
        ).update({"is_active": False})
        
        # 启用指定配置
        config.is_active = True
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise Exception(f"设置活跃模型配置失败: {str(e)}")
