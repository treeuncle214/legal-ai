# backend/database/models.py
"""
ORM 模型定义（纯模型，不包含业务逻辑）
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.database.engine import Base
from backend.config import SCORING_DIMENSIONS


# ==================== 动态生成评分维度列 ====================

def create_submission_fields():
    """根据 SCORING_DIMENSIONS 动态创建提交表的评分字段"""
    fields = {}
    for dim in SCORING_DIMENSIONS:
        key = dim["key"]
        fields[f"score_{key}"] = Column(Float, nullable=True)          # AI原始分
        fields[f"level_{key}"] = Column(String(10), nullable=True)     # 等级
        fields[f"final_score_{key}"] = Column(Float, nullable=True)    # 教师调整分
    return fields


# ==================== 模型定义 ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "display_name": self.display_name or self.username,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(String(50), nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Integer, default=1)
    max_submissions = Column(Integer, default=3)
    allow_after_deadline = Column(Integer, default=0)
    
    task_type = Column(String(20), default="任务实践")
    enabled_indicators = Column(String(500), default="")
    custom_prompt = Column(Text, nullable=True)

    def get_enabled_indicators_list(self):
        if not self.enabled_indicators:
            return []
        return [s.strip() for s in self.enabled_indicators.split(",") if s.strip()]
    
    def is_indicator_enabled(self, indicator_key):
        enabled = self.get_enabled_indicators_list()
        if not enabled:
            return True
        return indicator_key in enabled
    
    def get_custom_prompt(self):
        return self.custom_prompt if self.custom_prompt else None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "is_active": self.is_active,
            "task_type": self.task_type,
            "enabled_indicators": self.enabled_indicators,
            "custom_prompt": self.custom_prompt
        }


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    student_username = Column(String(100), nullable=False, index=True)
    
    # 提交内容
    process_log = Column(Text, nullable=True)
    ai_interaction_log = Column(Text, nullable=True)
    final_output = Column(Text, nullable=True)
    tools_used = Column(Text, nullable=True)
    
    # Word 提交
    word_file_path = Column(String(500), nullable=True)
    word_content = Column(Text, nullable=True)
    submit_type = Column(String(20), default="text")
    
    # AI 评分
    ai_comment = Column(Text, nullable=True)
    
    # 教师审批
    is_reviewed = Column(Integer, default=0)
    teacher_comment = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # ========== 新增：成绩是否已对学生公布 ==========
    score_published = Column(Integer, default=0)  # 0=未公布，1=已公布
    
    # 元数据
    submit_time = Column(DateTime, default=datetime.now)
    resubmit_count = Column(Integer, default=0)

    # 关系
    task = relationship("Task", backref="submissions")

    def get_scores_dict(self):
        """获取评分字典（优先使用final_score）"""
        result = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            final_score = getattr(self, f"final_score_{key}", None)
            if final_score is not None and final_score > 0:
                result[key] = final_score
            else:
                result[key] = getattr(self, f"score_{key}", 0.0)
        return result
    
    def get_levels_dict(self):
        result = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            result[key] = getattr(self, f"level_{key}", "")
        return result
    
    def get_dimension_score(self, dimension_key):
        final = getattr(self, f"final_score_{dimension_key}", None)
        if final is not None and final > 0:
            return final
        return getattr(self, f"score_{dimension_key}", 0.0)
    
    def calculate_weighted_total(self):
        total = 0.0
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            weight = dim.get("weight", 0.2)
            score = self.get_dimension_score(key)
            total += score * weight
        return round(total, 2)

    def to_dict(self, include_scores=True):
        """
        转换为字典
        include_scores: 是否包含评分信息（学生端根据score_published控制）
        """
        result = {
            "id": self.id,
            "task_id": self.task_id,
            "student_username": self.student_username,
            "process_log": self.process_log,
            "ai_interaction_log": self.ai_interaction_log,
            "final_output": self.final_output,
            "tools_used": self.tools_used,
            "word_file_path": self.word_file_path,
            "word_content": self.word_content,
            "submit_type": self.submit_type,
            "ai_comment": self.ai_comment,
            "is_reviewed": self.is_reviewed,
            "teacher_comment": self.teacher_comment,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if self.reviewed_at else None,
            "submit_time": self.submit_time.strftime("%Y-%m-%d %H:%M:%S") if self.submit_time else None,
            "resubmit_count": self.resubmit_count,
            "task_title": self.task.title if self.task else None,
            "score_published": self.score_published,  # 新增
        }
        
        # 只有 include_scores=True 时才返回评分信息
        if include_scores:
            result["scores"] = self.get_scores_dict()
            result["levels"] = self.get_levels_dict()
            result["weighted_total"] = self.calculate_weighted_total()
            
            # 保留原始动态字段
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                result[f"score_{key}"] = getattr(self, f"score_{key}", None)
                result[f"level_{key}"] = getattr(self, f"level_{key}", None)
                result[f"final_score_{key}"] = getattr(self, f"final_score_{key}", None)
        
        return result


class Rubric(Base):
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


# 动态添加评分维度列
submission_attrs = create_submission_fields()
for attr_name, column in submission_attrs.items():
    setattr(Submission, attr_name, column)