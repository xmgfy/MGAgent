from sqlalchemy.orm import Session
from app.db.models import SecurityRule
from datetime import datetime
import uuid
from typing import Optional


def create_security_rule(
    db: Session,
    rule_type: str,
    content: str,
    action: str = 'mask',
    priority: int = 0,
    description: Optional[str] = None,
    tenant_id: Optional[str] = None,
    is_active: bool = True,
) -> SecurityRule:
    rule = SecurityRule(
        id=str(uuid.uuid4()),
        rule_type=rule_type,
        content=content,
        action=action,
        priority=priority,
        description=description,
        tenant_id=tenant_id,
        is_active=is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_security_rule_by_id(db: Session, rule_id: str) -> Optional[SecurityRule]:
    return db.query(SecurityRule).filter(SecurityRule.id == rule_id).first()


def get_security_rules(
    db: Session,
    is_active: Optional[bool] = None,
    tenant_id: Optional[str] = None,
) -> list[SecurityRule]:
    query = db.query(SecurityRule)
    if is_active is not None:
        query = query.filter(SecurityRule.is_active == is_active)
    if tenant_id is not None:
        query = query.filter(
            (SecurityRule.tenant_id == None) | (SecurityRule.tenant_id == tenant_id)
        )
    return query.order_by(SecurityRule.priority.desc()).all()


def update_security_rule(db: Session, rule_id: str, **kwargs) -> Optional[SecurityRule]:
    rule = get_security_rule_by_id(db, rule_id)
    if rule:
        for key, value in kwargs.items():
            setattr(rule, key, value)
        rule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rule)
    return rule


def delete_security_rule(db: Session, rule_id: str) -> bool:
    rule = get_security_rule_by_id(db, rule_id)
    if rule:
        db.delete(rule)
        db.commit()
        return True
    return False


def toggle_security_rule(db: Session, rule_id: str) -> Optional[SecurityRule]:
    rule = get_security_rule_by_id(db, rule_id)
    if rule:
        rule.is_active = not rule.is_active
        rule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rule)
    return rule
