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

    # 关系：教师管理的班级
    managed_classes = relationship("Class", back_populates="teacher", foreign_keys="Class.teacher_id")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "display_name": self.display_name or self.username,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class Class(Base):
    """班级表"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, nullable=True)  # 预留：未来课程扩展
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    teacher = relationship("User", back_populates="managed_classes", foreign_keys=[teacher_id])
    students = relationship("UserClass", back_populates="class_ref")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.display_name if self.teacher else None,
            "course_id": self.course_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "student_count": len(self.students) if self.students else 0
        }


class UserClass(Base):
    """学生-班级关联表"""
    __tablename__ = "user_class"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User")
    class_ref = relationship("Class", back_populates="students")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "class_id": self.class_id,
            "joined_at": self.joined_at.strftime("%Y-%m-%d %H:%M:%S") if self.joined_at else None
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
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    course_id = Column(Integer, nullable=True)  # 预留：未来课程扩展
    
    task_type = Column(String(20), default="任务实践")
    enabled_indicators = Column(String(500), default="")
    custom_prompt = Column(Text, nullable=True)
     # ========== 新增：评分关联 ==========
    rubric_template_id = Column(Integer, ForeignKey("rubric_templates.id"), nullable=True)  # 关联的评分模板
    task_rubric_id = Column(Integer, ForeignKey("task_rubrics.id"), nullable=True)          # 关联的评分配置快照




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
            "class_id": self.class_id,  # 新增
            "course_id": self.course_id  # 新增
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
    original_filenames = Column(Text, nullable=True) 
    
    # AI 评分
    ai_comment = Column(Text, nullable=True)
    
    # 教师审批
    is_reviewed = Column(Integer, default=0)
    teacher_comment = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # 成绩是否已对学生公布
    score_published = Column(Integer, default=0)
    
    # 元数据
    submit_time = Column(DateTime, default=datetime.now)
    resubmit_count = Column(Integer, default=0)

    # 关系
    task = relationship("Task", backref="submissions")

    def get_scores_dict(self):
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
            "score_published": self.score_published,
        }
        
        if include_scores:
            result["scores"] = self.get_scores_dict()
            result["levels"] = self.get_levels_dict()
            result["weighted_total"] = self.calculate_weighted_total()
            
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



# ==================== 新增：评分模板 ====================

class RubricTemplate(Base):
    """评分模板表 - 教师可创建可复用的评分配置"""
    __tablename__ = "rubric_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)                # 模板名称
    description = Column(Text, nullable=True)                 # 模板描述
    task_type = Column(String(20), nullable=True)             # 适用类型：课堂练习/任务实践/综合考察
    overall_prompt = Column(Text, nullable=True)              # 作业级提示词（1份）
    created_by = Column(String(100), nullable=False)          # 创建者用户名
    share_type = Column(String(20), default="private")        # private / shared / public
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
    indicator_key = Column(String(10), nullable=False)        # A1, A2, B1, ...
    max_score = Column(Integer, nullable=False)               # 该指标满分
    prompt = Column(Text, nullable=True)                      # 指标级提示词
    sort_order = Column(Integer, default=0)                   # 排序

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
    shared_with = Column(String(100), nullable=False)         # 被共享的教师用户名
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "template_id": self.template_id,
            "shared_with": self.shared_with,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


# ==================== 新增：任务评分配置（快照） ====================

class TaskRubric(Base):
    """任务评分配置表 - 每次任务的评分配置快照"""
    __tablename__ = "task_rubrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, unique=True)
    template_id = Column(Integer, ForeignKey("rubric_templates.id"), nullable=True)  # 来源模板（可为空）
    overall_prompt = Column(Text, nullable=True)              # 作业级提示词（快照）
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
    prompt = Column(Text, nullable=True)                      # 指标级提示词（快照）
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


# ==================== 新增：提交评分详情 ====================

class SubmissionScore(Base):
    """提交评分详情表 - 存储每个二级指标的得分"""
    __tablename__ = "submission_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    indicator_key = Column(String(10), nullable=False)        # A1, A2, ...
    score = Column(Float, nullable=False)                     # 实际得分
    level = Column(String(10), nullable=False)                # 优/良/合格/不合格
    comment = Column(Text, nullable=True)                     # 该指标评语
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "indicator_key": self.indicator_key,
            "score": self.score,
            "level": self.level,
            "comment": self.comment,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


# ==================== 新增：学期总评 ====================

class TermScore(Base):
    """学期总评表 - 学期结束时计算快照"""
    __tablename__ = "term_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_username = Column(String(100), nullable=False, index=True)
    
    # 课程总成绩
    course_total_score = Column(Float, nullable=True)
    
    # 四个一级维度综合得分
    A_ai_retrieval_score = Column(Float, nullable=True)
    B_critical_score = Column(Float, nullable=True)
    C_ethics_score = Column(Float, nullable=True)
    D_integration_score = Column(Float, nullable=True)
    
    # 四个一级维度等级
    A_ai_retrieval_level = Column(String(10), nullable=True)
    B_critical_level = Column(String(10), nullable=True)
    C_ethics_level = Column(String(10), nullable=True)
    D_integration_level = Column(String(10), nullable=True)
    
    # 13个二级指标综合得分
    A1_score = Column(Float, nullable=True)
    A2_score = Column(Float, nullable=True)
    A3_score = Column(Float, nullable=True)
    A4_score = Column(Float, nullable=True)
    B1_score = Column(Float, nullable=True)
    B2_score = Column(Float, nullable=True)
    B3_score = Column(Float, nullable=True)
    C1_score = Column(Float, nullable=True)
    C2_score = Column(Float, nullable=True)
    C3_score = Column(Float, nullable=True)
    D1_score = Column(Float, nullable=True)
    D2_score = Column(Float, nullable=True)
    D3_score = Column(Float, nullable=True)
    
    # 13个二级指标等级
    A1_level = Column(String(10), nullable=True)
    A2_level = Column(String(10), nullable=True)
    A3_level = Column(String(10), nullable=True)
    A4_level = Column(String(10), nullable=True)
    B1_level = Column(String(10), nullable=True)
    B2_level = Column(String(10), nullable=True)
    B3_level = Column(String(10), nullable=True)
    C1_level = Column(String(10), nullable=True)
    C2_level = Column(String(10), nullable=True)
    C3_level = Column(String(10), nullable=True)
    D1_level = Column(String(10), nullable=True)
    D2_level = Column(String(10), nullable=True)
    D3_level = Column(String(10), nullable=True)
    
    # 统计信息
    exercise_count = Column(Integer, default=0)               # 课堂练习次数
    practice_count = Column(Integer, default=0)               # 任务实践次数
    final_count = Column(Integer, default=0)                  # 综合考察次数
    
    # 学情点评（教师可编辑）
    teacher_summary = Column(Text, nullable=True)             # 教师撰写的学期点评
    
    generated_at = Column(DateTime, default=datetime.now)     # 生成时间

    def to_dict(self):
        return {
            "id": self.id,
            "student_username": self.student_username,
            "course_total_score": self.course_total_score,
            "A_ai_retrieval_score": self.A_ai_retrieval_score,
            "B_critical_score": self.B_critical_score,
            "C_ethics_score": self.C_ethics_score,
            "D_integration_score": self.D_integration_score,
            "A_ai_retrieval_level": self.A_ai_retrieval_level,
            "B_critical_level": self.B_critical_level,
            "C_ethics_level": self.C_ethics_level,
            "D_integration_level": self.D_integration_level,
            "exercise_count": self.exercise_count,
            "practice_count": self.practice_count,
            "final_count": self.final_count,
            "teacher_summary": self.teacher_summary,
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S") if self.generated_at else None
        }