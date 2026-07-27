"""
数据库模块统一导出
"""

from backend.database.engine import get_db, get_db_session, SessionLocal, engine, Base

# ============================================================
# 模型导入
# ============================================================
from backend.database.models import (
    User, Class, UserClass, Task, Submission, Rubric,
    RubricTemplate, RubricTemplateIndicator, TemplateShare,
    TaskRubric, TaskRubricIndicator, SubmissionScore, TermScore,
)

# ============================================================
# 用户操作
# ============================================================
from backend.database.users import (
    add_user, get_user, get_all_students, get_all_users, delete_user,
    get_user_by_id, get_user_by_session
)

# ============================================================
# 任务操作
# ============================================================
from backend.database.tasks import (
    add_task, get_task, get_all_tasks, update_task, delete_task
)

# ============================================================
# ✅ 提交操作（从 submissions/ 包导入）
# ============================================================
from backend.database.submissions import (
    add_submission,
    update_scores,
    update_scores_v2,
    update_ai_score_status,
    get_submission,
    get_submission_by_file_path,
    get_submissions_by_student_v2,
    get_submissions_by_task_v2,
    get_submissions_by_task,
    get_submissions_by_task_all,
    review_submission,
    get_all_submissions_summary,
    publish_submission_score,
    get_published_submissions_for_student,
    get_student_submissions_without_scores,
    get_submission_for_review,
    get_student_class_info,
    get_submission_count,
    get_submission_count_v2,
    can_submit,
    can_submit_v2,
)

# ============================================================
# ✅ 兼容旧函数名（别名）
# ============================================================
get_submissions_by_student = get_submissions_by_student_v2
get_submissions_by_task = get_submissions_by_task_v2
get_submission_count = get_submission_count_v2
can_submit = can_submit_v2

# ============================================================
# 班级操作
# ============================================================
from backend.database.classes import (
    create_class, get_class, get_teacher_classes, get_class_students,
    add_student_to_class, remove_student_from_class, get_student_class_ids
)

# ============================================================
# 画像
# ============================================================
from backend.database.profile import (
    get_student_profile, calculate_profile, get_dimension_scores_history
)

# ============================================================
# 迁移
# ============================================================
from backend.database.migrations import init_db, ensure_task_columns, ensure_submission_columns

# ============================================================
# 模板操作
# ============================================================
from backend.database.rubric import (
    create_template, get_template, get_templates_by_teacher,
    update_template, delete_template, update_template_indicators,
    share_template_with_teacher, remove_template_share,
    create_task_rubric_snapshot, get_task_rubric,
    update_task_rubric_task_id
)

# ============================================================
# 学期总评
# ============================================================
from backend.database.term_scores import (
    calculate_term_score, save_term_score, get_term_score, get_all_term_scores
)


__all__ = [
    # 引擎
    "get_db", "get_db_session", "SessionLocal", "engine", "Base",
    
    # 模型
    "User", "Class", "UserClass", "Task", "Submission", "Rubric",
    "RubricTemplate", "RubricTemplateIndicator", "TemplateShare",
    "TaskRubric", "TaskRubricIndicator", "SubmissionScore", "TermScore",
    
    # 用户操作
    "add_user", "get_user", "get_user_by_id", "get_user_by_session",
    "get_all_students", "get_all_users", "delete_user",
    
    # 任务操作
    "add_task", "get_task", "get_all_tasks", "update_task", "delete_task",
    
    # ✅ 提交操作
    "add_submission",
    "update_scores", "update_scores_v2", "update_ai_score_status",
    "get_submission", "get_submission_by_file_path",
    "get_submissions_by_student_v2", "get_submissions_by_task_v2",
    "get_submissions_by_task", "get_submissions_by_task_all",
    "review_submission", "get_all_submissions_summary",
    "publish_submission_score",
    "get_published_submissions_for_student",
    "get_student_submissions_without_scores",
    "get_submission_for_review", "get_student_class_info",
    "get_submission_count", "get_submission_count_v2",
    "can_submit", "can_submit_v2",
    # ✅ 兼容旧函数名
    "get_submissions_by_student",
    "get_submissions_by_task",
    "get_submission_count",
    "can_submit",
    
    # 班级操作
    "create_class", "get_class", "get_teacher_classes", "get_class_students",
    "add_student_to_class", "remove_student_from_class", "get_student_class_ids",
    
    # 画像
    "get_student_profile", "calculate_profile", "get_dimension_scores_history",
    
    # 迁移
    "init_db", "ensure_task_columns", "ensure_submission_columns",
    
    # 模板操作
    "create_template", "get_template", "get_templates_by_teacher",
    "update_template", "delete_template", "update_template_indicators",
    "share_template_with_teacher", "remove_template_share",
    "create_task_rubric_snapshot", "get_task_rubric", "update_task_rubric_task_id",
    
    # 学期总评
    "calculate_term_score", "save_term_score", "get_term_score", "get_all_term_scores",
]