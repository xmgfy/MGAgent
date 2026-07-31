"""
用户管理相关 Schema
"""
from pydantic import BaseModel


class UpdateUserStatusRequest(BaseModel):
    """更新用户状态请求"""
    status: str


class UpdateUserRoleRequest(BaseModel):
    """更新用户角色请求"""
    role: str