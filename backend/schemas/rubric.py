# backend/schemas/rubric.py
"""
评分模板相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import Optional, List


class IndicatorConfig(BaseModel):
    """指标配置"""
    indicator_key: str
    max_score: int
    prompt: Optional[str] = None


class RubricTemplateCreate(BaseModel):
    """创建评分模板"""
    name: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    overall_prompt: Optional[str] = None
    share_type: str = "private"
    indicators: List[IndicatorConfig]


class RubricTemplateUpdate(BaseModel):
    """更新评分模板"""
    name: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    overall_prompt: Optional[str] = None
    share_type: Optional[str] = None
    indicators: Optional[List[IndicatorConfig]] = None


class RubricTemplateResponse(BaseModel):
    """评分模板响应"""
    id: int
    name: str
    description: Optional[str]
    task_type: Optional[str]
    overall_prompt: Optional[str]
    created_by: str
    share_type: str
    created_at: str
    updated_at: Optional[str]
    indicators: List[IndicatorConfig]
    shared_with: Optional[List[str]] = []
    is_shared: bool = False
    share_source: Optional[str] = None


class ShareTemplateRequest(BaseModel):
    """共享模板请求"""
    teacher_username: str


class TaskRubricResponse(BaseModel):
    """任务评分配置响应"""
    id: int
    task_id: int
    template_id: Optional[int]
    overall_prompt: Optional[str]
    indicators: List[IndicatorConfig]
    created_at: str
