"""
任务评分配置（快照）模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from backend.database.engine import Base


class TaskRubric(Base):
    """任务评分配置表 - 每次任务的评分配置快照"""
    __tablename__ = "task_rubrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, unique=True)
    template_id = Column(Integer, ForeignKey("rubric_templates.id"), nullable=True)
    overall_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "template_id": self.template_id,
            "overall_prompt": self.overall_prompt,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class TaskRubricIndicator(Base):
    """任务评分配置-指标关联表"""
    __tablename__ = "task_rubric_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_rubric_id = Column(Integer, ForeignKey("task_rubrics.id"), nullable=False)
    indicator_key = Column(String(10), nullable=False)
    max_score = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "task_rubric_id": self.task_rubric_id,
            "indicator_key": self.indicator_key,
            "max_score": self.max_score,
            "prompt": self.prompt,
            "sort_order": self.sort_order
        }