from sqlalchemy.orm import Session
from app.db.models import ModelConfig
from datetime import datetime
import uuid

def create_model_config(db: Session, name: str, api_key: str, api_base: str, model_name: str) -> ModelConfig:
    config = ModelConfig(
        id=str(uuid.uuid4()),
        name=name,
        api_key=api_key,
        api_base=api_base,
        model_name=model_name,
        is_active=False,
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
    for config in db.query(ModelConfig).filter(ModelConfig.is_active == True).all():
        config.is_active = False
        config.updated_at = datetime.utcnow()
    
    config = get_model_config_by_id(db, config_id)
    if config:
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
