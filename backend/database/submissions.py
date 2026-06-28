# backend/database/submissions.py
"""
提交 CRUD 操作
"""

from datetime import datetime
from sqlalchemy import func
from backend.database.engine import SessionLocal
from backend.database.models import Submission
from backend.config import SCORING_DIMENSIONS
from typing import List, Dict, Any, Optional
import sqlite3
from backend.database.engine import get_db_connection
import logging

logger = logging.getLogger(__name__)


def add_submission(
    task_id: int,
    student_username: str,
    process_log: str = "",
    ai_interaction_log: str = "",
    final_output: str = "",
    tools_used: str = "",
    submit_type: str = "text",
    word_file_path: str = None,
    word_content: str = None,
    ai_score_status: str = "pending",
    is_reviewed: int = 0
) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        submit_time = datetime.now().isoformat()

        if word_file_path is None:
            word_file_path = ""
        if word_content is None:
            word_content = ""

        cursor.execute("""
            INSERT INTO submissions (
                task_id, student_username, process_log, ai_interaction_log,
                final_output, tools_used, submit_type, word_file_path, word_content,
                submit_time, ai_score_status, is_reviewed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, student_username, process_log, ai_interaction_log,
            final_output, tools_used, submit_type, word_file_path, word_content,
            submit_time, ai_score_status, is_reviewed
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"添加提交记录失败: {e}")
        raise
    finally:
        conn.close()


def update_scores(submission_id, scores_dict):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            for key, value in scores_dict.items():
                if hasattr(submission, key):
                    setattr(submission, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_submissions_by_student(student_username):
    db = SessionLocal()
    try:
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username
        ).order_by(Submission.submit_time.desc()).all()
        return [s.to_dict() for s in submissions]
    finally:
        db.close()


def get_submissions_by_task(task_id: int) -> List[Dict]:
    """
    获取某任务下每个学生的最新提交记录（教师端使用）
    只返回最新一条提交（按 id 最大）
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, u.display_name as student_name 
            FROM submissions s
            JOIN users u ON s.student_username = u.username
            WHERE s.id IN (
                SELECT MAX(id) 
                FROM submissions 
                WHERE task_id = ? 
                GROUP BY student_username
            )
            ORDER BY s.submit_time DESC
        """, (task_id,))
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"获取任务提交记录失败: {e}")
        return []
    finally:
        conn.close()


def get_submissions_by_task_all(task_id: int) -> List[Dict]:
    """
    获取某任务下所有提交记录（学生端用，或需要历史记录时）
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, u.display_name as student_name 
            FROM submissions s 
            JOIN users u ON s.student_username = u.username 
            WHERE s.task_id = ? 
            ORDER BY s.submit_time DESC
        """, (task_id,))
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"获取任务提交记录失败: {e}")
        return []
    finally:
        conn.close()


def review_submission(submission_id, teacher_username, scores_dict, teacher_comment=""):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.is_reviewed = 1
            submission.teacher_comment = teacher_comment
            submission.reviewed_by = teacher_username
            submission.reviewed_at = datetime.now()
            
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                if key in scores_dict:
                    setattr(submission, f"final_score_{key}", scores_dict[key])
            
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_all_submissions_summary():
    db = SessionLocal()
    try:
        from backend.database.models import User
        
        avg_columns = []
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            avg_columns.append(
                func.avg(func.coalesce(
                    getattr(Submission, f"final_score_{key}"),
                    getattr(Submission, f"score_{key}")
                )).label(f"avg_{key}")
            )
        
        query = db.query(
            Submission.student_username,
            *avg_columns,
            func.count(Submission.id).label("task_count")
        ).group_by(Submission.student_username).order_by(Submission.student_username)
        
        rows = query.all()
        
        students = {s.username: s.display_name for s in db.query(User).filter(User.role == "student").all()}
        
        return [
            {
                "student_username": row.student_username,
                "student_display_name": students.get(row.student_username, row.student_username),
                **{dim["key"]: round(getattr(row, f"avg_{dim['key']}") or 0, 1) for dim in SCORING_DIMENSIONS},
                "task_count": row.task_count
            }
            for row in rows
        ]
    finally:
        db.close()


def get_submission_count(student_username, task_id):
    db = SessionLocal()
    try:
        count = db.query(Submission).filter(
            Submission.student_username == student_username,
            Submission.task_id == task_id
        ).count()
        return count
    finally:
        db.close()


def can_submit(student_username, task_id, task):
    from datetime import datetime
    
    if task.due_date and not task.allow_after_deadline:
        due_date = datetime.fromisoformat(task.due_date) if isinstance(task.due_date, str) else task.due_date
        if datetime.now() > due_date:
            return False, "任务已截止，无法提交"
    
    submission_count = get_submission_count(student_username, task_id)
    if submission_count >= task.max_submissions:
        return False, f"提交次数已达上限（{task.max_submissions}次）"
    
    return True, f"还可以提交{task.max_submissions - submission_count}次"


def update_ai_score_status(submission_id: int, status: str, error_message: str = None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if error_message:
            cursor.execute(
                "UPDATE submissions SET ai_score_status = ?, ai_score_error = ? WHERE id = ?",
                (status, error_message, submission_id)
            )
        else:
            cursor.execute(
                "UPDATE submissions SET ai_score_status = ? WHERE id = ?",
                (status, submission_id)
            )
        conn.commit()
        logger.info(f"提交 {submission_id} AI评分状态更新为: {status}")
    except Exception as e:
        logger.error(f"更新AI评分状态失败: {e}")
        raise
    finally:
        conn.close()


def update_scores_v2(submission_id: int, scores_dict: dict):
    """更新评分（增强版，支持状态更新）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        set_clauses = []
        params = []
        
        allowed_fields = [
            'score_ai_retrieval', 'score_critical', 'score_ethics', 'score_integration',
            'ai_comment', 'ai_score_status', 'ai_score_error', 'ai_score_detail'
        ]
        
        for key, value in scores_dict.items():
            if key in allowed_fields:
                set_clauses.append(f"{key} = ?")
                params.append(value)
        
        if not set_clauses:
            logger.warning(f"没有有效的字段更新: {scores_dict.keys()}")
            return
        
        params.append(submission_id)
        
        query = f"UPDATE submissions SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        logger.info(f"提交 {submission_id} 评分更新成功")
    except Exception as e:
        logger.error(f"更新评分失败: {e}")
        raise
    finally:
        conn.close()


def can_submit_v2(student_username: str, task_id: int, task_obj) -> tuple:
    conn = get_db_connection()
    from datetime import datetime
    
    try:
        cursor = conn.cursor()
        
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
        print(f"检查提交权限失败: {e}")
        return False, f"检查失败: {str(e)}"
    finally:
        conn.close()


def get_submission_count_v2(student_username: str, task_id: int) -> int:
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


def get_submission(submission_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"获取提交记录失败: {e}")
        return None
    finally:
        conn.close()


def get_submissions_by_student_v2(student_username: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.*, t.title as task_title 
               FROM submissions s 
               JOIN tasks t ON s.task_id = t.id 
               WHERE s.student_username = ? 
               ORDER BY s.submit_time DESC""",
            (student_username,)
        )
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"获取学生提交记录失败: {e}")
        return []
    finally:
        conn.close()


def get_submissions_by_task_v2(task_id: int) -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, u.display_name as student_name 
            FROM submissions s 
            JOIN users u ON s.student_username = u.username 
            WHERE s.task_id = ? 
            ORDER BY s.submit_time DESC
        """, (task_id,))
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"获取任务提交记录失败: {e}")
        return []
    finally:
        conn.close()


def delete_submission(submission_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))
        conn.commit()
        logger.info(f"已删除提交记录 {submission_id}")
    except Exception as e:
        logger.error(f"删除提交记录失败: {e}")
        raise
    finally:
        conn.close()


def publish_submission_score(submission_id: int) -> bool:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE submissions SET score_published = 1 WHERE id = ?",
            (submission_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"发布成绩失败: {e}")
        raise
    finally:
        conn.close()


def get_published_submissions_for_student(student_username: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, t.title as task_title 
            FROM submissions s 
            JOIN tasks t ON s.task_id = t.id 
            WHERE s.student_username = ? 
            AND s.score_published = 1
            AND s.is_reviewed = 1
            ORDER BY s.submit_time DESC
        """, (student_username,))
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        results = []
        for row in rows:
            data = dict(zip(columns, row))
            total = 0.0
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                weight = dim.get("weight", 0.2)
                score = data.get(f"final_score_{key}") or data.get(f"score_{key}") or 0
                total += score * weight
            data["weighted_total"] = round(total, 2)
            results.append(data)
        return results
    except Exception as e:
        logger.error(f"获取已发布成绩失败: {e}")
        return []
    finally:
        conn.close()


def get_student_submissions_without_scores(student_username: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                s.id, s.task_id, s.student_username, 
                s.process_log, s.ai_interaction_log, s.final_output,
                s.tools_used, s.word_file_path, s.word_content,
                s.submit_type, s.is_reviewed, s.teacher_comment, 
                s.submit_time, s.score_published, t.title as task_title
            FROM submissions s 
            JOIN tasks t ON s.task_id = t.id 
            WHERE s.student_username = ? 
            ORDER BY s.submit_time DESC
        """, (student_username,))
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"获取学生提交记录失败: {e}")
        return []
    finally:
        conn.close()


def get_submission_for_review(submission_id: int, include_scores: bool = True) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        if not row:
            return None
        columns = [description[0] for description in cursor.description]
        result = dict(zip(columns, row))
        
        if include_scores:
            total = 0.0
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                weight = dim.get("weight", 0.2)
                score = result.get(f"final_score_{key}") or result.get(f"score_{key}") or 0
                total += score * weight
            result["weighted_total"] = round(total, 2)
        
        return result
    except Exception as e:
        logger.error(f"获取提交详情失败: {e}")
        return None
    finally:
        conn.close()