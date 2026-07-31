"""
Schema 模块
"""
from app.schemas.common import ApiResponse, ErrorResponse, PaginationParams, PaginationInfo, PaginatedResponse
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
    TokenResponse,
    RegisterResponse,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageResponse,
    SessionResponse,
    SessionDetailResponse,
    UpdateSessionRequest,
)
from app.schemas.document import DocumentResponse
from app.schemas.user import UpdateUserStatusRequest, UpdateUserRoleRequest

__all__ = [
    # 通用
    "ApiResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginationInfo",
    "PaginatedResponse",
    # 认证
    "LoginRequest",
    "RegisterRequest",
    "UserResponse",
    "TokenResponse",
    "RegisterResponse",
    # 聊天
    "ChatRequest",
    "ChatResponse",
    "MessageResponse",
    "SessionResponse",
    "SessionDetailResponse",
    "UpdateSessionRequest",
    # 文档
    "DocumentResponse",
    # 用户
    "UpdateUserStatusRequest",
    "UpdateUserRoleRequest",
]