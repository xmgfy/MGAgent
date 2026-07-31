"""
依赖注入模块
"""
from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.crud import get_user
from app.core.security import decode_access_token
from app.exceptions import UnauthorizedException
from app.db.models import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                return get_user(db, user_id)
        return None
    except Exception:
        return None


async def get_authenticated_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """获取已认证用户（必填）"""
    user = await get_current_user(authorization, db)
    if not user:
        raise UnauthorizedException("请先登录")
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """获取可选用户（允许匿名访问）"""
    return await get_current_user(authorization, db)
