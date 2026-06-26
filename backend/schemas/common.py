# backend/schemas/common.py
"""
通用 Pydantic 模型
"""

from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


# backend/schemas/common.py
class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: Optional[str] = None  # 改为可选
    token_type: str = "bearer"
    username: str
    role: str
    display_name: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str