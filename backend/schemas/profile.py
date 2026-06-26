"""
画像相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import Dict, List, Optional


class DimensionScore(BaseModel):
    """单个维度分数"""
    score: float
    status: str  # "evaluated" 或 "pending"
    name: str
    weight: float
    latest_exercise: Optional[float] = None
    latest_final: Optional[float] = None


class DimensionProfile(BaseModel):
    """维度画像"""
    dimensions: Dict[str, DimensionScore]
    overall: float
    missing_dimensions: List[str]
    last_submit_time: Optional[str] = None


class ProfileResponse(BaseModel):
    """画像API响应"""
    username: str
    display_name: Optional[str]
    dimensions: Dict[str, DimensionScore]
    overall_score: float
    missing_dimensions: List[str]
    history: Dict[str, List[float]]
    evaluated_indicators: List[str]
    pending_indicators: List[str]


class IndicatorInfo(BaseModel):
    """二级指标信息"""
    key: str
    name: str
    dimension: str
    description: Optional[str] = None


class DimensionConfigResponse(BaseModel):
    """维度配置响应"""
    dimensions: List[Dict]
    indicators: List[IndicatorInfo]
    dimension_keys: List[str]