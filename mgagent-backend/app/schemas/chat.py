"""
聊天相关 Schema
"""
from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    response: str


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    created_at: str


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    title: str
    created_at: str
    updated_at: str


class SessionDetailResponse(SessionResponse):
    """会话详情响应"""
    messages: list[MessageResponse] = []


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    title: str