from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import Admin
from app.db.crud.security import (
    create_security_rule,
    get_security_rules,
    get_security_rule_by_id,
    update_security_rule,
    delete_security_rule,
    toggle_security_rule,
)
from .auth import get_current_admin

router = APIRouter()


class SecurityRuleRequest(BaseModel):
    rule_type: str  # 'keyword', 'regex'
    content: str
    action: str = 'mask'  # 'block', 'mask'
    priority: int = 0
    description: Optional[str] = None


class SecurityRuleUpdateRequest(BaseModel):
    rule_type: Optional[str] = None
    content: Optional[str] = None
    action: Optional[str] = None
    priority: Optional[int] = None
    description: Optional[str] = None


class SecurityRuleResponse(BaseModel):
    id: str
    tenant_id: Optional[str]
    rule_type: str
    content: str
    action: str
    priority: int
    is_active: bool
    description: Optional[str]
    created_at: str
    updated_at: str


@router.get("/security/rules", response_model=List[SecurityRuleResponse])
async def list_security_rules(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    is_active: Optional[bool] = None,
):
    """获取安全规则列表"""
    rules = get_security_rules(db, is_active=is_active, tenant_id=admin.tenant_id)
    return [
        SecurityRuleResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            rule_type=r.rule_type,
            content=r.content,
            action=r.action,
            priority=r.priority,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            description=r.description,
            created_at=r.created_at.isoformat() if r.created_at else '',
            updated_at=r.updated_at.isoformat() if r.updated_at else '',
        )
        for r in rules
    ]


@router.post("/security/rules", response_model=SecurityRuleResponse)
async def create_rule(
    request: SecurityRuleRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """创建安全规则"""
    if request.rule_type not in ('keyword', 'regex'):
        raise HTTPException(status_code=400, detail="rule_type 必须为 keyword 或 regex")
    if request.action not in ('block', 'mask'):
        raise HTTPException(status_code=400, detail="action 必须为 block 或 mask")
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="content 不能为空")

    # 如果是正则，验证合法性
    if request.rule_type == 'regex':
        import re
        try:
            re.compile(request.content)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"正则表达式无效: {e}")

    rule = create_security_rule(
        db,
        rule_type=request.rule_type,
        content=request.content,
        action=request.action,
        priority=request.priority,
        description=request.description,
        tenant_id=admin.tenant_id,
    )
    return SecurityRuleResponse(
        id=rule.id,
        tenant_id=rule.tenant_id,
        rule_type=rule.rule_type,
        content=rule.content,
        action=rule.action,
        priority=rule.priority,
        is_active=bool(rule.is_active) if rule.is_active is not None else True,
        description=rule.description,
        created_at=rule.created_at.isoformat() if rule.created_at else '',
        updated_at=rule.updated_at.isoformat() if rule.updated_at else '',
    )


@router.put("/security/rules/{rule_id}", response_model=SecurityRuleResponse)
async def update_rule(
    rule_id: str,
    request: SecurityRuleUpdateRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """更新安全规则"""
    rule = get_security_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="安全规则不存在")

    update_data = {}
    if request.rule_type is not None:
        if request.rule_type not in ('keyword', 'regex'):
            raise HTTPException(status_code=400, detail="rule_type 必须为 keyword 或 regex")
        update_data['rule_type'] = request.rule_type
    if request.content is not None:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="content 不能为空")
        update_data['content'] = request.content
    if request.action is not None:
        if request.action not in ('block', 'mask'):
            raise HTTPException(status_code=400, detail="action 必须为 block 或 mask")
        update_data['action'] = request.action
    if request.priority is not None:
        update_data['priority'] = request.priority
    if request.description is not None:
        update_data['description'] = request.description

    # 正则验证
    final_type = update_data.get('rule_type', rule.rule_type)
    final_content = update_data.get('content', rule.content)
    if final_type == 'regex':
        import re
        try:
            re.compile(final_content)
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"正则表达式无效: {e}")

    updated = update_security_rule(db, rule_id, **update_data)
    return SecurityRuleResponse(
        id=updated.id,
        tenant_id=updated.tenant_id,
        rule_type=updated.rule_type,
        content=updated.content,
        action=updated.action,
        priority=updated.priority,
        is_active=bool(updated.is_active) if updated.is_active is not None else True,
        description=updated.description,
        created_at=updated.created_at.isoformat() if updated.created_at else '',
        updated_at=updated.updated_at.isoformat() if updated.updated_at else '',
    )


@router.post("/security/rules/{rule_id}/toggle", response_model=SecurityRuleResponse)
async def toggle_rule(
    rule_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """启用/停用安全规则"""
    rule = get_security_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="安全规则不存在")

    toggled = toggle_security_rule(db, rule_id)
    return SecurityRuleResponse(
        id=toggled.id,
        tenant_id=toggled.tenant_id,
        rule_type=toggled.rule_type,
        content=toggled.content,
        action=toggled.action,
        priority=toggled.priority,
        is_active=bool(toggled.is_active) if toggled.is_active is not None else True,
        description=toggled.description,
        created_at=toggled.created_at.isoformat() if toggled.created_at else '',
        updated_at=toggled.updated_at.isoformat() if toggled.updated_at else '',
    )


@router.delete("/security/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除安全规则"""
    rule = get_security_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="安全规则不存在")

    if delete_security_rule(db, rule_id):
        return {"message": "安全规则已删除"}
    raise HTTPException(status_code=500, detail="删除失败")


@router.post("/security/test")
async def test_filter(
    request: dict,
    admin: Admin = Depends(get_current_admin),
):
    """测试内容过滤效果（不写入数据库）"""
    import re

    test_content = request.get('content', '')
    if not test_content:
        raise HTTPException(status_code=400, detail="请输入测试内容")

    # 内置规则（与 mgagent-backend/content_filter.py 保持一致）
    builtin_keywords = [
        'system prompt', '系统提示词', 'prompt内容', 'api_key', 'api密钥',
        'secret_key', '数据库结构', 'database schema', 'password', '密码',
        'token', '密钥', 'secret', 'credential',
    ]
    builtin_patterns = [
        (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP地址]'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[邮箱]'),
        (r'\b1[3-9]\d{9}\b', '[手机号]'),
        (r'\b\d{17}[\dXx]\b', '[身份证号]'),
    ]

    filtered = test_content
    matched = []

    for kw in builtin_keywords:
        if kw.lower() in filtered.lower():
            matched.append({'type': 'keyword', 'content': kw, 'action': 'mask'})
            filtered = re.sub(re.escape(kw), '[已过滤]', filtered, flags=re.IGNORECASE)

    for pattern, replacement in builtin_patterns:
        if re.search(pattern, filtered, re.IGNORECASE):
            matched.append({'type': 'pattern', 'content': pattern, 'action': 'mask'})
            filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)

    return {
        'original': test_content,
        'filtered': filtered,
        'has_sensitive': len(matched) > 0,
        'matched_rules': matched,
    }
