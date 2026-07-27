"""
基础工具函数
"""

from sqlalchemy import Column, Float, String
from backend.config import SCORING_DIMENSIONS


def create_submission_fields():
    """根据 SCORING_DIMENSIONS 动态创建提交表的评分字段"""
    fields = {}
    for dim in SCORING_DIMENSIONS:
        key = dim["key"]
        fields[f"score_{key}"] = Column(Float, nullable=True)          # AI原始分
        fields[f"level_{key}"] = Column(String(10), nullable=True)     # 等级
        fields[f"final_score_{key}"] = Column(Float, nullable=True)    # 教师调整分
    return fields