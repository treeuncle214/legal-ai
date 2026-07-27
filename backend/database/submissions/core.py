"""
提交核心 CRUD 操作
"""

from datetime import datetime
from typing import List, Dict, Optional
import logging

from backend.database.engine import get_db_connection
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
    ai_scored: bool = False,  # 🆕 新增参数
    ai_scored_at: str = None,  # 🆕 新增参数
    ai_scored_by: str = None   # 🆕 新增参数
) -> int:
    """添加提交记录"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        submit_time = datetime.now().isoformat()

        if word_file_path is None:
            word_file_path = ""
        if word_content is None:
            word_content = ""
        if original_filenames is None:
            original_filenames = ""

        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 基础字段
        base_fields = [
            'task_id', 'student_username', 'process_log', 'ai_interaction_log',
            'final_output', 'tools_used', 'submit_type', 'word_file_path', 'word_content',
            'submit_time', 'ai_score_status', 'is_reviewed', 'original_filenames'
        ]
        base_values = [
            task_id, student_username, process_log, ai_interaction_log,
            final_output, tools_used, submit_type, word_file_path, word_content,
            submit_time, ai_score_status, is_reviewed, original_filenames
        ]
        
        # 检查 ai_scored 字段是否存在
        if 'ai_scored' in columns:
            base_fields.append('ai_scored')
            base_values.append(1 if ai_scored else 0)
        
        # 检查 ai_scored_at 字段是否存在
        if 'ai_scored_at' in columns and ai_scored_at:
            base_fields.append('ai_scored_at')
            base_values.append(ai_scored_at)
        
        # 检查 ai_scored_by 字段是否存在
        if 'ai_scored_by' in columns and ai_scored_by:
            base_fields.append('ai_scored_by')
            base_values.append(ai_scored_by)
        
        # 构建 SQL
        placeholders = ','.join(['?'] * len(base_fields))
        fields_str = ','.join(base_fields)
        
        cursor.execute(f"""
            INSERT INTO submissions ({fields_str})
            VALUES ({placeholders})
        """, tuple(base_values))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        logger.error(f"添加提交记录失败: {e}")
        raise
    finally:
        conn.close()


def get_submission(submission_id: int) -> Optional[Dict]:
    """获取单条提交记录（原始dict）"""
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


def delete_submission(submission_id: int):
    """删除提交记录"""
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


def get_submission_by_file_path(filename: str) -> Optional[Dict]:
    """根据存储的文件名查找提交记录"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, word_file_path, original_filenames 
            FROM submissions 
            WHERE word_file_path LIKE ?
        """, (f"%{filename}%",))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "word_file_path": row[1], "original_filenames": row[2]}
        return None
    except Exception as e:
        logger.error(f"查询提交记录失败: {e}")
        return None
    finally:
        conn.close()


def get_submissions_by_student_v2(student_username: str) -> List[Dict]:
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


def get_submissions_by_task_v2(task_id: int) -> List[Dict]:
    """获取某任务的所有提交记录"""
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


def update_submission_ai_scored(submission_id: int, ai_scored: bool = True, ai_scored_by: str = None):
    """更新提交的AI评分状态"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        updates = ["ai_scored = ?"]
        values = [1 if ai_scored else 0]
        
        if 'ai_scored_at' in columns:
            updates.append("ai_scored_at = ?")
            values.append(now)
        
        if 'ai_scored_by' in columns and ai_scored_by:
            updates.append("ai_scored_by = ?")
            values.append(ai_scored_by)
        
        values.append(submission_id)
        
        cursor.execute(f"""
            UPDATE submissions 
            SET {', '.join(updates)}
            WHERE id = ?
        """, tuple(values))
        conn.commit()
        logger.info(f"已更新提交 {submission_id} 的AI评分状态")
    except Exception as e:
        logger.error(f"更新AI评分状态失败: {e}")
        raise
    finally:
        conn.close()