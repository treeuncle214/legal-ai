"""
用户相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import Optional, List


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    password: str
    role: str = "student"
    display_name: Optional[str] = None
    college: Optional[str] = ""      # 🆕 学院
    major: Optional[str] = ""        # 🆕 专业


class UserUpdate(BaseModel):
    """更新用户请求"""
    password: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    college: Optional[str] = None    # 🆕 学院
    major: Optional[str] = None      # 🆕 专业


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    role: str
    display_name: str
    college: Optional[str] = ""      # 🆕 学院
    major: Optional[str] = ""        # 🆕 专业
    created_at: Optional[str] = None


class BatchUsersRequest(BaseModel):
    """批量导入用户请求"""
    users: List[UserCreate]


class BatchUsersResponse(BaseModel):
    """批量导入用户响应"""
    success_count: int
    fail_count: int
    failed_users: List[str] = []