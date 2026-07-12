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
    enabled_indicators: str = ""  # 逗号分隔的二级指标（兼容旧版）
    custom_prompt: Optional[str] = None  # 自定义AI评分提示词
    class_id: int  # 所属班级ID（必填）
    # ========== 新增：评分模板关联 ==========
    rubric_template_id: Optional[int] = None  # 使用已有模板ID
    # 或者直接传入临时配置
    rubric_config: Optional[dict] = None  # 临时配置 {"indicators": [{"key": "A1", "max_score": 20, "prompt": "..."}], "overall_prompt": "..."}
    weight: Optional[float] = None  # 作业权重（如 5, 8, 40）
    max_submissions: int = 3
    allow_after_deadline: int = 0


class TaskUpdate(BaseModel):
    """更新任务请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    is_active: Optional[int] = None
    task_type: Optional[str] = None
    enabled_indicators: Optional[str] = None
    custom_prompt: Optional[str] = None
    class_id: Optional[int] = None
    rubric_template_id: Optional[int] = None
    weight: Optional[float] = None
    max_submissions: Optional[int] = None
    allow_after_deadline: Optional[int] = None


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
    custom_prompt: Optional[str] = None
    class_id: Optional[int] = None
    rubric_template_id: Optional[int] = None
    weight: Optional[float] = None
    max_submissions: int = 3
    allow_after_deadline: int = 0


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskResponse]
    total: int