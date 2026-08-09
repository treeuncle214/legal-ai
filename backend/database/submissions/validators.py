"""
提交权限校验
"""

from datetime import datetime
from typing import Tuple
import logging

from backend.database.engine import SessionLocal
from backend.database.models import Submission

logger = logging.getLogger(__name__)


def get_submission_count(student_username: str, task_id: int) -> int:
    """获取学生某任务的提交次数"""
    db = SessionLocal()
    try:
        count = db.query(Submission).filter(
            Submission.student_username == student_username,
            Submission.task_id == task_id
        ).count()
        return count
    finally:
        db.close()


def can_submit(student_username: str, task_id: int, task) -> Tuple[bool, str]:
    """检查学生是否可以提交"""
    if task.due_date and not task.allow_after_deadline:
        due_date = datetime.fromisoformat(task.due_date) if isinstance(task.due_date, str) else task.due_date
        if datetime.now() > due_date:
            return False, "任务已截止，无法提交"

    submission_count = get_submission_count(student_username, task_id)
    if submission_count >= task.max_submissions:
        return False, f"提交次数已达上限（{task.max_submissions}次）"

    return True, f"还可以提交{task.max_submissions - submission_count}次"