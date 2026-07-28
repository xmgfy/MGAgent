"""
模型配置服务 - Admin Backend
从数据库读取模型配置，无兜底逻辑
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.db.models import ModelConfig
from app.db.database import get_session


def get_active_model_config(db: Session = None) -> Dict[str, Any]:
    """获取当前活跃的模型配置，无配置时抛出异常"""
    if db is None:
        db = get_session()
    
    try:
        config = db.query(ModelConfig).filter(ModelConfig.is_active == True).first()
        if not config:
            raise ValueError("未配置活跃的模型，请在模型管理中配置并启用模型")
        
        return {
            "id": config.id,
            "name": config.name,
            "api_key": config.api_key,
            "api_base": config.api_base,
            "model_name": config.model_name,
            "is_active": config.is_active
        }
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"获取模型配置失败: {e}")


def get_embeddings_model(db: Session = None):
    """获取嵌入模型实例，无配置时抛出异常"""
    model_config = get_active_model_config(db)
    
    try:
        from langchain_openai import OpenAIEmbeddings
        
        return OpenAIEmbeddings(
            api_key=model_config["api_key"],
            base_url=model_config["api_base"],
            model="text-embedding-3-small"
        )
    except ImportError:
        raise ImportError("langchain_openai 未安装，请执行: pip install langchain-openai")
    except Exception as e:
        raise Exception(f"初始化嵌入模型失败: {str(e)}")
