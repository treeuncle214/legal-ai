"""
任务和提交模型
"""

from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from backend.database.engine import Base, SessionLocal
from backend.config import SCORING_DIMENSIONS, get_level_by_score
from backend.database.models.base import create_submission_fields


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
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    course_id = Column(Integer, nullable=True)
    
    task_type = Column(String(20), default="任务实践")
    enabled_indicators = Column(String(500), default="")
    custom_prompt = Column(Text, nullable=True)
    
    rubric_template_id = Column(Integer, ForeignKey("rubric_templates.id"), nullable=True)
    task_rubric_id = Column(Integer, ForeignKey("task_rubrics.id"), nullable=True)

    weight = Column(Integer, default=5)
    
    attachment_path = Column(String(500), nullable=True)
    attachment_filename = Column(String(200), nullable=True)


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
            "custom_prompt": self.custom_prompt,
            "class_id": self.class_id,
            "course_id": self.course_id,
            "rubric_template_id": self.rubric_template_id,
            "task_rubric_id": self.task_rubric_id,
            "max_submissions": self.max_submissions,
            "allow_after_deadline": self.allow_after_deadline,
            "weight": self.weight,
            "attachment_path": self.attachment_path,
            "attachment_filename": self.attachment_filename,
            "has_attachment": bool(self.attachment_path)   
        }


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    student_username = Column(String(100), nullable=False, index=True)
    
    process_log = Column(Text, nullable=True)
    ai_interaction_log = Column(Text, nullable=True)
    final_output = Column(Text, nullable=True)
    tools_used = Column(Text, nullable=True)
    
    word_file_path = Column(String(500), nullable=True)
    word_content = Column(Text, nullable=True)
    submit_type = Column(String(20), default="text")
    original_filenames = Column(Text, nullable=True) 
    
    ai_comment = Column(Text, nullable=True)
    
    # ========== AI评分状态字段 ==========
    ai_score_status = Column(String(20), default="pending")
    ai_score_error = Column(Text, nullable=True)
    ai_score_detail = Column(Text, nullable=True)
    
    # ========== AI评分控制字段 ==========
    ai_scored = Column(Boolean, default=False, nullable=False)
    ai_scored_at = Column(DateTime, nullable=True)
    ai_scored_by = Column(String(50), nullable=True)
    
    # ========== 测评报告字段 ==========
    evaluation_report = Column(Text, nullable=True)
    report_generated_at = Column(DateTime, nullable=True)

    # ========== 教师审批字段 ==========
    is_reviewed = Column(Integer, default=0)
    teacher_comment = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    score_published = Column(Integer, default=0)
    
    submit_time = Column(DateTime, default=datetime.now)
    resubmit_count = Column(Integer, default=0)

    # ✅ 总分字段（保存每次作业的总分）
    total_score = Column(Float, default=0.0)

    # 关系
    task = relationship("Task", backref="submissions")

    def get_dimension_score(self, dimension_key: str) -> float:
        final_score = getattr(self, f"final_score_{dimension_key}", None)
        if final_score is not None and final_score > 0:
            return float(final_score)
        score = getattr(self, f"score_{dimension_key}", None)
        if score is not None:
            return float(score)
        return 0.0
    
    def get_scores_dict(self) -> Dict:
        result = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            result[key] = self.get_dimension_score(key)
        return result
    
    def get_levels_dict(self) -> Dict:
        result = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            final_score = getattr(self, f"final_score_{key}", None)
            if final_score is not None and final_score > 0:
                result[key] = get_level_by_score(final_score)
            else:
                result[key] = getattr(self, f"level_{key}", "")
        return result
    
    def calculate_weighted_total(self) -> float:
        """已弃用：使用 total_score 字段代替"""
        return self.total_score or 0.0

    def to_dict(self, include_scores=True):
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
            "ai_score_status": self.ai_score_status,
            "ai_score_error": self.ai_score_error,
            "ai_score_detail": self.ai_score_detail,
            "ai_scored": self.ai_scored,
            "ai_scored_at": self.ai_scored_at.strftime("%Y-%m-%d %H:%M:%S") if self.ai_scored_at else None,
            "ai_scored_by": self.ai_scored_by,
            "evaluation_report": self.evaluation_report,
            "report_generated_at": self.report_generated_at.strftime("%Y-%m-%d %H:%M:%S") if self.report_generated_at else None,
            "is_reviewed": self.is_reviewed,
            "teacher_comment": self.teacher_comment,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if self.reviewed_at else None,
            "submit_time": self.submit_time.strftime("%Y-%m-%d %H:%M:%S") if self.submit_time else None,
            "resubmit_count": self.resubmit_count,
            "task_title": self.task.title if self.task else None,
            "score_published": self.score_published,
            "total_score": self.total_score,  # ✅ 添加
        }
        
        if include_scores:
            result["scores"] = self.get_scores_dict()
            result["levels"] = self.get_levels_dict()
            result["weighted_total"] = self.total_score or 0.0
            
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                result[f"score_{key}"] = getattr(self, f"score_{key}", None)
                result[f"level_{key}"] = getattr(self, f"level_{key}", None)
                result[f"final_score_{key}"] = getattr(self, f"final_score_{key}", None)
        
        return result


# 动态添加评分维度列（必须在类定义之后执行）
submission_attrs = create_submission_fields()
for attr_name, column in submission_attrs.items():
    setattr(Submission, attr_name, column)