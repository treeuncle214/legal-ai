"""
评分标准（Rubric）和评分模板（RubricTemplate）模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.database.engine import Base


class Rubric(Base):
    """评分标准表（预设等级描述）"""
    __tablename__ = "rubric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dimension = Column(String(100), nullable=False)
    level = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    min_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "dimension": self.dimension,
            "level": self.level,
            "description": self.description,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }


class RubricTemplate(Base):
    """评分模板表 - 教师可创建可复用的评分配置"""
    __tablename__ = "rubric_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(20), nullable=True)
    overall_prompt = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False)
    share_type = Column(String(20), default="private")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "overall_prompt": self.overall_prompt,
            "created_by": self.created_by,
            "share_type": self.share_type,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }


class RubricTemplateIndicator(Base):
    """模板-指标关联表（每个指标独立的提示词）"""
    __tablename__ = "rubric_template_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("rubric_templates.id"), nullable=False)
    indicator_key = Column(String(10), nullable=False)
    max_score = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "template_id": self.template_id,
            "indicator_key": self.indicator_key,
            "max_score": self.max_score,
            "prompt": self.prompt,
            "sort_order": self.sort_order
        }


class TemplateShare(Base):
    """模板共享表 - 记录模板共享给哪些教师"""
    __tablename__ = "template_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("rubric_templates.id"), nullable=False)
    shared_with = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "template_id": self.template_id,
            "shared_with": self.shared_with,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
