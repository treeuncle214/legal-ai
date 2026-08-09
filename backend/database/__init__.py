"""
数据库模块统一导出
"""

from backend.database.engine import get_db_session, SessionLocal, engine, Base

from backend.database.models import (
    User, Class, UserClass, Task, Submission, Rubric,
    RubricTemplate, RubricTemplateIndicator, TemplateShare,
    TaskRubric, TaskRubricIndicator, SubmissionScore, TermScore,
)

from backend.database.users import (
    add_user, get_user, get_all_students, get_all_users, delete_user,
    get_user_by_id, get_user_by_session
)

from backend.database.tasks import (
    add_task, get_task, get_all_tasks, update_task, delete_task
)

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
    can_submit,
)

# 兼容旧函数名（别名）
get_submissions_by_student = get_submissions_by_student_v2
get_submissions_by_task = get_submissions_by_task_v2

from backend.database.classes import (
    create_class, get_class, get_teacher_classes, get_class_students,
    add_student_to_class, remove_student_from_class, get_student_class_ids
)

from backend.database.profile import (
    get_student_profile, calculate_profile, get_dimension_scores_history
)

from backend.database.migrations import init_db, ensure_task_columns, ensure_submission_columns

from backend.database.rubric import (
    create_template, get_template, get_templates_by_teacher,
    update_template, delete_template, update_template_indicators,
    share_template_with_teacher, remove_template_share,
    create_task_rubric_snapshot, get_task_rubric,
    update_task_rubric_task_id
)

from backend.database.term_scores import (
    calculate_term_score, save_term_score, get_term_score, get_all_term_scores
)


__all__ = [
    "get_db_session", "SessionLocal", "engine", "Base",

    "User", "Class", "UserClass", "Task", "Submission", "Rubric",
    "RubricTemplate", "RubricTemplateIndicator", "TemplateShare",
    "TaskRubric", "TaskRubricIndicator", "SubmissionScore", "TermScore",

    "add_user", "get_user", "get_user_by_id", "get_user_by_session",
    "get_all_students", "get_all_users", "delete_user",

    "add_task", "get_task", "get_all_tasks", "update_task", "delete_task",

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
    "get_submission_count", "can_submit",
    "get_submissions_by_student",

    "create_class", "get_class", "get_teacher_classes", "get_class_students",
    "add_student_to_class", "remove_student_from_class", "get_student_class_ids",

    "get_student_profile", "calculate_profile", "get_dimension_scores_history",

    "init_db", "ensure_task_columns", "ensure_submission_columns",

    "create_template", "get_template", "get_templates_by_teacher",
    "update_template", "delete_template", "update_template_indicators",
    "share_template_with_teacher", "remove_template_share",
    "create_task_rubric_snapshot", "get_task_rubric", "update_task_rubric_task_id",

    "calculate_term_score", "save_term_score", "get_term_score", "get_all_term_scores",
]