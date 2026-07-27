"""
提交权限校验（次数检查、截止日期检查）
"""

from datetime import datetime
from typing import Tuple
import logging

from backend.database.engine import get_db_connection
from backend.database.engine import SessionLocal
from backend.database.models import Submission

logger = logging.getLogger(__name__)


def get_submission_count(student_username: str, task_id: int) -> int:
    """获取学生某任务的提交次数（SQLAlchemy）"""
    db = SessionLocal()
    try:
        count = db.query(Submission).filter(
            Submission.student_username == student_username,
            Submission.task_id == task_id
        ).count()
        return count
    finally:
        db.close()


def get_submission_count_v2(student_username: str, task_id: int) -> int:
    """获取学生某任务的提交次数（原生SQL，支持状态过滤）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM submissions 
            WHERE student_username = ? AND task_id = ?
        """, (student_username, task_id))
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        logger.error(f"获取提交次数失败: {e}")
        return 0
    finally:
        conn.close()


def can_submit(student_username: str, task_id: int, task) -> Tuple[bool, str]:
    """
    检查学生是否可以提交（SQLAlchemy版本）
    """
    if task.due_date and not task.allow_after_deadline:
        due_date = datetime.fromisoformat(task.due_date) if isinstance(task.due_date, str) else task.due_date
        if datetime.now() > due_date:
            return False, "任务已截止，无法提交"
    
    submission_count = get_submission_count(student_username, task_id)
    if submission_count >= task.max_submissions:
        return False, f"提交次数已达上限（{task.max_submissions}次）"
    
    return True, f"还可以提交{task.max_submissions - submission_count}次"


def can_submit_v2(student_username: str, task_id: int, task_obj) -> Tuple[bool, str]:
    """
    检查学生是否可以提交（原生SQL版本，更高效）
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 只统计已完成的提交（不计入正在评分中的）
        cursor.execute("""
            SELECT COUNT(*) FROM submissions 
            WHERE student_username = ? 
            AND task_id = ? 
            AND ai_score_status = 'completed'
        """, (student_username, task_id))
        count = cursor.fetchone()[0]
        
        if count >= task_obj.max_submissions:
            return False, f"提交次数已达上限（{task_obj.max_submissions}次）"
        
        if task_obj.due_date and not task_obj.allow_after_deadline:
            due_date = datetime.fromisoformat(task_obj.due_date) if isinstance(task_obj.due_date, str) else task_obj.due_date
            if datetime.now() > due_date:
                return False, "任务已截止，无法提交"
        
        return True, "可以提交"
    except Exception as e:
        logger.error(f"检查提交权限失败: {e}")
        return False, f"检查失败: {str(e)}"
    finally:
        conn.close()