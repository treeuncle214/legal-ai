"""
提交 CRUD 操作
"""

from datetime import datetime
from sqlalchemy import func
from backend.database.engine import SessionLocal
from backend.database.models import Submission
from backend.config import SCORING_DIMENSIONS
from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
from backend.database.engine import get_db_connection  # 添加这一行
import logging

logger = logging.getLogger(__name__)

# backend/database/submissions.py
# backend/database/submissions.py

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
    is_reviewed: int = 0   # 新参数，默认0
) -> int:
    from datetime import datetime
    from backend.database.engine import get_db_connection

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
    """
    更新AI评分
    scores_dict 格式：
    {
        "score_ai_retrieval": 85,
        "level_ai_retrieval": "B",
        "score_critical": 78,
        "comment": "评语"
    }
    """
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


# backend/database/submissions.py

def add_submission(
    task_id: int,
    student_username: str,
    process_log: str = "",
    ai_interaction_log: str = "",
    final_output: str = "",
    tools_used: str = "",
    submit_type: str = "text",
    word_file_path: str = "",
    word_content: str = "",
    ai_score_status: str = "pending"  # 添加这个参数
) -> int:
    """
    添加提交记录
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 获取当前时间
        submit_time = datetime.now().isoformat()
        
        # 插入记录
        cursor.execute("""
            INSERT INTO submissions (
                task_id, student_username, process_log, ai_interaction_log,
                final_output, tools_used, submit_type, word_file_path, word_content,
                submit_time, ai_score_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, student_username, process_log, ai_interaction_log,
            final_output, tools_used, submit_type, word_file_path, word_content,
            submit_time, ai_score_status
        ))
        
        conn.commit()
        return cursor.lastrowid
        
    except Exception as e:
        logger.error(f"添加提交记录失败: {e}")
        raise
    finally:
        conn.close()


def get_submissions_by_student(student_username):
    db = SessionLocal()
    try:
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username
        ).order_by(Submission.submit_time.desc()).all()
        return [s.to_dict() for s in submissions]
    finally:
        db.close()


def get_submissions_by_task(task_id):
    db = SessionLocal()
    try:
        submissions = db.query(Submission).filter(
            Submission.task_id == task_id
        ).order_by(Submission.submit_time.desc()).all()
        return [s.to_dict() for s in submissions]
    finally:
        db.close()


def review_submission(submission_id, teacher_username, scores_dict, teacher_comment=""):
    """
    教师审批
    scores_dict 格式：{"ai_retrieval": 85, "critical": 78, ...}
    """
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
    """获取全班成绩汇总"""
    db = SessionLocal()
    try:
        from backend.database.models import User
        
        # 构建平均分查询
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
        
        # 获取学生显示名
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
    """获取学生在某个任务下的提交次数"""
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
    """检查是否可以提交"""
    from datetime import datetime
    
    # 1. 检查截止时间
    if task.due_date and not task.allow_after_deadline:
        due_date = datetime.fromisoformat(task.due_date) if isinstance(task.due_date, str) else task.due_date
        if datetime.now() > due_date:
            return False, "任务已截止，无法提交"
    
    # 2. 检查提交次数
    submission_count = get_submission_count(student_username, task_id)
    if submission_count >= task.max_submissions:
        return False, f"提交次数已达上限（{task.max_submissions}次）"
    
    return True, f"还可以提交{task.max_submissions - submission_count}次"

# backend/database/submissions.py 中添加以下函数

def update_ai_score_status(submission_id: int, status: str, error_message: str = None):
    """更新AI评分状态"""
    from backend.database.engine import get_db_connection
    
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
        print(f"✅ 更新提交 {submission_id} 状态为: {status}")
    except Exception as e:
        print(f"更新状态失败: {e}")
        raise
    finally:
        conn.close()


def update_scores(submission_id: int, scores_dict: dict):
    """更新评分（增强版，支持状态更新）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 构建动态更新语句
        set_clauses = []
        params = []
        
        for key, value in scores_dict.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        params.append(submission_id)
        
        query = f"UPDATE submissions SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    finally:
        conn.close()

# backend/database/submissions.py

def update_ai_score_status(submission_id: int, status: str, error_message: str = None):
    """更新AI评分状态"""
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


def update_scores(submission_id: int, scores_dict: dict):
    """更新评分（增强版，支持状态更新）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 构建动态更新语句
        set_clauses = []
        params = []
        
        # 定义允许更新的字段
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


def can_submit(student_username: str, task_id: int, task_obj) -> tuple:
    """检查学生是否可以提交"""
    from backend.database.engine import get_db_connection
    from datetime import datetime
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 只统计成功的提交
        cursor.execute("""
            SELECT COUNT(*) FROM submissions 
            WHERE student_username = ? 
            AND task_id = ? 
            AND ai_score_status = 'completed'
        """, (student_username, task_id))
        count = cursor.fetchone()[0]
        
        print(f"检查提交权限 - 学生: {student_username}, 任务: {task_id}, 成功提交次数: {count}, 最大次数: {task_obj.max_submissions}")
        
        # 检查是否超过最大提交次数
        if count >= task_obj.max_submissions:
            return False, f"提交次数已达上限（{task_obj.max_submissions}次）"
        
        # 检查是否超过截止时间
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


def get_submission_count(student_username: str, task_id: int) -> int:
    """统计学生在某任务下的所有提交记录（不限状态）"""
    from backend.database.engine import get_db_connection
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
    """获取单条提交记录"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        if row:
            # 将row转换为字典
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"获取提交记录失败: {e}")
        return None
    finally:
        conn.close()


def get_submissions_by_student(student_username: str) -> List[Dict]:
    """获取学生的所有提交记录"""
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


def get_submissions_by_task(task_id: int) -> List[Dict]:
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
    """删除提交记录（用于AI评分失败时）"""
    from backend.database.engine import get_db_connection
    
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
    
# backend/database/submissions.py
# 在文件末尾添加以下函数


def publish_submission_score(submission_id: int) -> bool:
    """
    发布成绩：将 score_published 设为 1
    """
    from backend.database.engine import get_db_connection
    
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
    """
    获取学生已发布成绩的提交记录（用于成绩总结页面）
    """
    from backend.database.engine import get_db_connection
    
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
            # 计算总分
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
    """
    获取提交详情，可控制是否返回评分信息
    """
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
            # 计算总分
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