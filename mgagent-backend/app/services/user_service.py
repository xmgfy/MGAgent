"""
用户服务层
"""
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.db.crud import (
    create_user,
    get_user,
    get_user_by_username,
    get_user_by_email,
    get_users,
    update_user_status,
    update_user_role,
    increment_chat_count,
    verify_password as verify_password_crud,
)
from app.db.models import User
from app.core.logger import logger
from app.exceptions import (
    NotFoundException,
    ValidationException,
    ForbiddenException,
)
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.auth import UserResponse


def _to_user_response(user: User) -> UserResponse:
    """转换为用户响应格式"""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        chat_count=user.chat_count,
        max_chats=user.max_chats,
        created_at=user.created_at.isoformat(),
    )


class UserService:
    """用户服务"""

    @staticmethod
    def login(
        db: Session,
        username: str,
        password: str,
    ) -> dict:
        """用户登录"""
        user = verify_password_crud(db, username, password)
        if not user:
            logger.warning(f"登录失败: 用户 {username} 密码错误")
            raise ValidationException("用户名或密码错误")

        # 检查用户状态
        status_map = {
            "pending": "账号尚未通过审批，请联系管理员",
            "frozen": "账号已被冻结，请联系管理员",
            "disabled": "账号已被禁用，请联系管理员",
            "rejected": "账号已被拒绝，请联系管理员",
        }
        if user.status in status_map:
            logger.warning(f"登录失败: 用户 {username} 状态为 {user.status}")
            raise ForbiddenException(status_map[user.status])

        # 创建访问令牌
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(f"用户登录成功: {username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": _to_user_response(user),
        }

    @staticmethod
    def register(
        db: Session,
        username: str,
        email: str,
        password: str,
    ) -> User:
        """用户注册"""
        if get_user_by_username(db, username):
            raise ValidationException("用户名已存在")
        if get_user_by_email(db, email):
            raise ValidationException("邮箱已被注册")

        user = create_user(db, username, email, password)
        logger.info(f"用户注册成功: {username}")
        return user

    @staticmethod
    def get_user_info(db: Session, user_id: str) -> User:
        """获取用户信息"""
        user = get_user(db, user_id)
        if not user:
            raise NotFoundException("用户不存在")
        return user

    @staticmethod
    def list_users(
        db: Session,
        status: Optional[str] = None,
    ) -> list[User]:
        """获取用户列表"""
        return get_users(db, status=status)

    @staticmethod
    def update_status(
        db: Session,
        user_id: str,
        status: str,
    ) -> User:
        """更新用户状态"""
        user = update_user_status(db, user_id, status)
        if not user:
            raise NotFoundException("用户不存在")
        logger.info(f"更新用户状态: {user_id} -> {status}")
        return user

    @staticmethod
    def update_role(
        db: Session,
        user_id: str,
        role: str,
    ) -> User:
        """更新用户角色"""
        user = update_user_role(db, user_id, role)
        if not user:
            raise NotFoundException("用户不存在")
        logger.info(f"更新用户角色: {user_id} -> {role}")
        return user

    @staticmethod
    def delete_user(db: Session, user_id: str) -> None:
        """删除用户"""
        user = get_user(db, user_id)
        if not user:
            raise NotFoundException("用户不存在")
        db.delete(user)
        db.commit()
        logger.info(f"删除用户: {user_id}")

    @staticmethod
    def increment_chat_count(db: Session, user_id: str) -> User:
        """增加聊天次数"""
        user = increment_chat_count(db, user_id)
        if not user:
            raise NotFoundException("用户不存在")
        return user
