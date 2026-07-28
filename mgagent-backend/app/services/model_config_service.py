"""
模型配置服务 - 从数据库读取和管理模型配置
所有模型配置统一从数据库获取，无兜底逻辑
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.db.models import ModelConfig
from app.db.database import get_session
import uuid


def get_active_model_config(db: Session = None) -> Dict[str, Any]:
    """获取当前活跃的模型配置，无配置时抛出异常"""
    if db is None:
        db = get_session()
    
    try:
        config = db.query(ModelConfig).filter(ModelConfig.is_active == True).first()
        if not config:
            raise ValueError("未配置活跃的模型，请在admin管理端配置并启用模型")
        
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


def get_model_config_by_id(config_id: str, db: Session = None) -> Optional[Dict[str, Any]]:
    """根据ID获取模型配置"""
    if db is None:
        db = get_session()
    
    try:
        config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
        if config:
            return {
                "id": config.id,
                "name": config.name,
                "api_key": config.api_key,
                "api_base": config.api_base,
                "model_name": config.model_name,
                "is_active": config.is_active
            }
        return None
    except Exception as e:
        raise Exception(f"获取模型配置失败: {e}")


def get_all_model_configs(db: Session = None) -> list:
    """获取所有模型配置"""
    if db is None:
        db = get_session()
    
    try:
        configs = db.query(ModelConfig).all()
        return [
            {
                "id": config.id,
                "name": config.name,
                "api_key": config.api_key[:4] + "****" + config.api_key[-4:] if len(config.api_key) > 8 else "****",
                "api_base": config.api_base,
                "model_name": config.model_name,
                "is_active": config.is_active
            }
            for config in configs
        ]
    except Exception as e:
        raise Exception(f"获取所有模型配置失败: {e}")


def create_model_config(config_data: Dict[str, Any], db: Session = None) -> Dict[str, Any]:
    """创建新的模型配置"""
    if db is None:
        db = get_session()
    
    try:
        # 如果设为活跃，则禁用其他配置
        if config_data.get("is_active"):
            db.query(ModelConfig).update({"is_active": False})
        
        config = ModelConfig(
            id=str(uuid.uuid4()),
            name=config_data["name"],
            api_key=config_data["api_key"],
            api_base=config_data["api_base"],
            model_name=config_data["model_name"],
            is_active=config_data.get("is_active", False)
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        
        return {
            "id": config.id,
            "name": config.name,
            "api_key": config.api_key[:4] + "****" + config.api_key[-4:] if len(config.api_key) > 8 else "****",
            "api_base": config.api_base,
            "model_name": config.model_name,
            "is_active": config.is_active
        }
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
        
        # 如果设为活跃，则禁用其他配置
        if config_data.get("is_active"):
            db.query(ModelConfig).update({"is_active": False})
        
        if "name" in config_data:
            config.name = config_data["name"]
        if "api_key" in config_data:
            config.api_key = config_data["api_key"]
        if "api_base" in config_data:
            config.api_base = config_data["api_base"]
        if "model_name" in config_data:
            config.model_name = config_data["model_name"]
        if "is_active" in config_data:
            config.is_active = config_data["is_active"]
        
        db.commit()
        db.refresh(config)
        
        return {
            "id": config.id,
            "name": config.name,
            "api_key": config.api_key[:4] + "****" + config.api_key[-4:] if len(config.api_key) > 8 else "****",
            "api_base": config.api_base,
            "model_name": config.model_name,
            "is_active": config.is_active
        }
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
    """设置活跃的模型配置"""
    if db is None:
        db = get_session()
    
    try:
        # 禁用所有配置
        db.query(ModelConfig).update({"is_active": False})
        
        # 启用指定配置
        config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
        if not config:
            raise Exception("模型配置不存在")
        
        config.is_active = True
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise Exception(f"设置活跃模型配置失败: {str(e)}")
