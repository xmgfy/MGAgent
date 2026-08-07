from sqlalchemy.orm import Session
from app.db.models import ModelConfig
from datetime import datetime
import uuid

def create_model_config(
    db: Session,
    name: str,
    model_name: str,
    model_type: str = "chat",
    provider: str = "openai",
    api_key: str = None,
    api_base: str = None,
    dimension: int = None,
    is_local: bool = False,
    scenario: str = None,
    tenant_id: str = None,
    temperature: float = None,
    top_p: float = None,
    max_tokens: int = None,
    presence_penalty: float = None,
    frequency_penalty: float = None
) -> ModelConfig:
    config = ModelConfig(
        id=str(uuid.uuid4()),
        name=name,
        model_type=model_type,
        provider=provider,
        api_key=api_key,
        api_base=api_base,
        model_name=model_name,
        dimension=dimension,
        is_local=is_local,
        is_active=False,
        scenario=scenario,
        tenant_id=tenant_id,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config

def get_model_config_by_id(db: Session, config_id: str) -> ModelConfig:
    return db.query(ModelConfig).filter(ModelConfig.id == config_id).first()

def get_model_config_by_name(db: Session, name: str) -> ModelConfig:
    return db.query(ModelConfig).filter(ModelConfig.name == name).first()

def get_model_configs(db: Session, is_active: bool = None) -> list[ModelConfig]:
    query = db.query(ModelConfig)
    if is_active is not None:
        query = query.filter(ModelConfig.is_active == is_active)
    return query.all()

def update_model_config(db: Session, config_id: str, **kwargs) -> ModelConfig:
    config = get_model_config_by_id(db, config_id)
    if config:
        for key, value in kwargs.items():
            setattr(config, key, value)
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
    return config

def set_active_model(db: Session, config_id: str) -> ModelConfig:
    config = get_model_config_by_id(db, config_id)
    if config:
        # 禁用同类型的其他配置
        for c in db.query(ModelConfig).filter(
            ModelConfig.model_type == config.model_type,
            ModelConfig.is_active == True
        ).all():
            c.is_active = False
            c.updated_at = datetime.utcnow()
        
        config.is_active = True
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
    return config

def deactivate_model(db: Session, config_id: str) -> ModelConfig:
    config = get_model_config_by_id(db, config_id)
    if config:
        config.is_active = False
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
    return config

def delete_model_config(db: Session, config_id: str) -> bool:
    config = get_model_config_by_id(db, config_id)
    if config:
        db.delete(config)
        db.commit()
        return True
    return False
