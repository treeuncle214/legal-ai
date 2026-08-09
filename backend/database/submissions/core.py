"""
提交核心 CRUD 操作
"""

from datetime import datetime
from typing import List, Dict, Optional
import logging

from sqlalchemy import text
from backend.database.engine import SessionLocal
from backend.database.models import Submission
from backend.config import SCORING_DIMENSIONS

logger = logging.getLogger(__name__)


def add_submission(
    task_id: int,
    student_username: str,
    process_log: str = None,
    ai_interaction_log: str = None,
    final_output: str = None,
    tools_used: str = None,
    submit_type: str = "text",
    word_file_path: str = None,
    word_content: str = None,
    ai_score_status: str = "pending",
    is_reviewed: int = 0,
    original_filenames: str = None,
    ai_scored: bool = False,
    ai_scored_at: str = None,
    ai_scored_by: str = None
) -> int:
    """添加提交记录"""
    db = SessionLocal()
    try:
        submit_time = datetime.now()

        submission = Submission(
            task_id=task_id,
            student_username=student_username,
            process_log=process_log,
            ai_interaction_log=ai_interaction_log,
            final_output=final_output,
            tools_used=tools_used,
            submit_type=submit_type,
            word_file_path=word_file_path or "",
            word_content=word_content or "",
            original_filenames=original_filenames or "",
            submit_time=submit_time,
            ai_score_status=ai_score_status,
            is_reviewed=is_reviewed,
            ai_scored=ai_scored,
            ai_scored_at=ai_scored_at,
            ai_scored_by=ai_scored_by
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission.id
    except Exception as e:
        db.rollback()
        logger.error(f"添加提交记录失败: {e}")
        raise
    finally:
        db.close()


def get_submission(submission_id: int) -> Optional[Dict]:
    """获取单条提交记录"""
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            return {c.name: getattr(submission, c.name) for c in submission.__table__.columns}
        return None
    except Exception as e:
        logger.error(f"获取提交记录失败: {e}")
        return None
    finally:
        db.close()


def delete_submission(submission_id: int):
    """删除提交记录"""
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            db.delete(submission)
            db.commit()
            logger.info(f"已删除提交记录 {submission_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"删除提交记录失败: {e}")
        raise
    finally:
        db.close()


def get_submission_by_file_path(filename: str) -> Optional[Dict]:
    """根据存储的文件名查找提交记录"""
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(
            Submission.word_file_path.like(f"%{filename}%")
        ).first()
        if submission:
            return {
                "id": submission.id,
                "word_file_path": submission.word_file_path,
                "original_filenames": submission.original_filenames
            }
        return None
    except Exception as e:
        logger.error(f"查询提交记录失败: {e}")
        return None
    finally:
        db.close()


def get_submissions_by_student_v2(student_username: str) -> List[Dict]:
    """获取学生的所有提交记录"""
    db = SessionLocal()
    try:
        from backend.database.models import Task
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username
        ).order_by(Submission.submit_time.desc()).all()

        results = []
        for s in submissions:
            task = db.query(Task).filter(Task.id == s.task_id).first()
            d = {c.name: getattr(s, c.name) for c in s.__table__.columns}
            d["task_title"] = task.title if task else None
            results.append(d)
        return results
    except Exception as e:
        logger.error(f"获取学生提交记录失败: {e}")
        return []
    finally:
        db.close()


def get_submissions_by_task_v2(task_id: int) -> List[Dict]:
    """获取某任务的所有提交记录"""
    db = SessionLocal()
    try:
        from backend.database.models import User
        submissions = db.query(Submission).filter(
            Submission.task_id == task_id
        ).order_by(Submission.submit_time.desc()).all()

        results = []
        for s in submissions:
            user = db.query(User).filter(User.username == s.student_username).first()
            d = {c.name: getattr(s, c.name) for c in s.__table__.columns}
            d["student_name"] = user.display_name if user else s.student_username
            results.append(d)
        return results
    except Exception as e:
        logger.error(f"获取任务提交记录失败: {e}")
        return []
    finally:
        db.close()


def get_submissions_by_task(task_id: int) -> List[Dict]:
    """获取某任务下每个学生的最新提交记录"""
    db = SessionLocal()
    try:
        from backend.database.models import User
        from sqlalchemy import func

        subquery = db.query(
            Submission.student_username,
            func.max(Submission.id).label("max_id")
        ).filter(Submission.task_id == task_id).group_by(Submission.student_username).subquery()

        submissions = db.query(Submission).join(
            subquery,
            Submission.id == subquery.c.max_id
        ).order_by(Submission.submit_time.desc()).all()

        results = []
        for s in submissions:
            user = db.query(User).filter(User.username == s.student_username).first()
            d = {c.name: getattr(s, c.name) for c in s.__table__.columns}
            d["student_name"] = user.display_name if user else s.student_username
            results.append(d)
        return results
    except Exception as e:
        logger.error(f"获取任务提交记录失败: {e}")
        return []
    finally:
        db.close()


def get_submissions_by_task_all(task_id: int) -> List[Dict]:
    """获取某任务下所有提交记录"""
    return get_submissions_by_task_v2(task_id)


def update_submission_ai_scored(submission_id: int, ai_scored: bool = True, ai_scored_by: str = None):
    """更新提交的AI评分状态"""
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.ai_scored = ai_scored
            submission.ai_scored_at = datetime.now().isoformat()
            if ai_scored_by:
                submission.ai_scored_by = ai_scored_by
            db.commit()
            logger.info(f"已更新提交 {submission_id} 的AI评分状态")
    except Exception as e:
        db.rollback()
        logger.error(f"更新AI评分状态失败: {e}")
        raise
    finally:
        db.close()