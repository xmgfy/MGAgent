"""
通用 Schema - 统一响应格式
"""
from typing import Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    code: str = "SUCCESS"
    data: Optional[T] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    code: str
    message: str
    detail: Optional[dict] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20


class PaginationInfo(BaseModel):
    """分页信息"""
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    code: str = "SUCCESS"
    data: list[T] = []
    pagination: Optional[PaginationInfo] = None
    message: Optional[str] = None
