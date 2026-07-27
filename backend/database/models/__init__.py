"""
数据库模型统一导出
保持与原有导入方式完全兼容
"""

from backend.database.models.base import create_submission_fields
from backend.database.models.user import User, Class, UserClass
from backend.database.models.task import Task, Submission
from backend.database.models.rubric import Rubric, RubricTemplate, RubricTemplateIndicator, TemplateShare
from backend.database.models.task_rubric import TaskRubric, TaskRubricIndicator
from backend.database.models.submission_score import SubmissionScore
from backend.database.models.term_score import TermScore

__all__ = [
    "create_submission_fields",
    "User",
    "Class",
    "UserClass",
    "Task",
    "Submission",
    "Rubric",
    "RubricTemplate",
    "RubricTemplateIndicator",
    "TemplateShare",
    "TaskRubric",
    "TaskRubricIndicator",
    "SubmissionScore",
    "TermScore",
]