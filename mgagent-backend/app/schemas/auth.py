"""
认证相关 Schema
"""
from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: str
    role: str
    status: str
    chat_count: int
    max_chats: int
    created_at: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str
    user: UserResponse


class RegisterResponse(BaseModel):
    """注册响应"""
    message: str
    user: UserResponse