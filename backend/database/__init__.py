"""
数据库模块统一导出
"""

from backend.database.engine import get_db, get_db_session, SessionLocal, engine, Base
from backend.database.models import User, Task, Submission, Rubric
from backend.database.users import (
    add_user, get_user, get_all_students, get_all_users, delete_user
)
from backend.database.tasks import (
    add_task, get_task, get_all_tasks, update_task, delete_task
)
from backend.database.submissions import (
    add_submission, update_scores, get_submission,
    get_submissions_by_student, get_submissions_by_task,
    review_submission, get_all_submissions_summary,
    publish_submission_score,  # 新增
    get_published_submissions_for_student,  # 新增
    get_student_submissions_without_scores,  # 新增
    get_submission_for_review  # 新增
)
from backend.database.profile import (
    get_student_profile, calculate_profile, get_dimension_scores_history
)
from backend.database.migrations import init_db, ensure_task_columns, ensure_submission_columns

__all__ = [
    # 引擎
    "get_db", "get_db_session", "SessionLocal", "engine", "Base",
    # 模型
    "User", "Task", "Submission", "Rubric",
    # 用户操作
    "add_user", "get_user", "get_all_students", "get_all_users", "delete_user",
    # 任务操作
    "add_task", "get_task", "get_all_tasks", "update_task", "delete_task",
    # 提交操作
    "add_submission", "update_scores", "get_submission",
    "get_submissions_by_student", "get_submissions_by_task",
    "review_submission", "get_all_submissions_summary",
    "publish_submission_score",  # 新增
    "get_published_submissions_for_student",  # 新增
    "get_student_submissions_without_scores",  # 新增
    "get_submission_for_review",  # 新增
    # 画像
    "get_student_profile", "calculate_profile", "get_dimension_scores_history",
    # 迁移
    "init_db", "ensure_task_columns", "ensure_submission_columns",
]