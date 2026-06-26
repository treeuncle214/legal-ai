# backend/schemas/task.py
"""
任务相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import Optional, List


class TaskCreate(BaseModel):
    """创建任务请求"""
    title: str
    description: Optional[str] = ""
    due_date: Optional[str] = None
    task_type: str = "任务实践"  # 课堂练习/任务实践/期末考察
    enabled_indicators: str = ""  # 逗号分隔的二级指标
    custom_prompt: Optional[str] = None  # 自定义AI评分提示词


class TaskUpdate(BaseModel):
    """更新任务请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    is_active: Optional[int] = None
    task_type: Optional[str] = None
    enabled_indicators: Optional[str] = None
    custom_prompt: Optional[str] = None  # 自定义AI评分提示词


class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[str]
    created_by: Optional[str]
    created_at: Optional[str]
    is_active: int
    task_type: str
    enabled_indicators: str
    custom_prompt: Optional[str] = None  # 自定义AI评分提示词


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskResponse]
    total: int