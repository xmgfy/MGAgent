"""
文档相关 Schema
"""
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: str