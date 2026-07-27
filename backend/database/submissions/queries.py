"""
提交复杂查询（已发布成绩、未评分记录、汇总统计等）
"""

from typing import List, Dict, Optional
import logging
import json  # ✅ 新增

from sqlalchemy import func
from backend.database.engine import get_db_connection, SessionLocal
from backend.database.models import Submission, User
from backend.config import SCORING_DIMENSIONS, get_level_by_score

logger = logging.getLogger(__name__)


def get_published_submissions_for_student(student_username: str) -> List[Dict]:
    """
    获取学生所有已发布的成绩
    ✅ 优先使用教师调整后的分数
    ✅ 包含测评报告作为教师评语
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, t.title as task_title, t.task_type
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
            
            # 查询指标得分
            cursor2 = conn.cursor()
            cursor2.execute("""
                SELECT indicator_key, score
                FROM submission_scores
                WHERE submission_id = ?
            """, (data["id"],))
            score_rows = cursor2.fetchall()
            
            # 构建指标得分字典
            indicator_scores = {}
            for sr in score_rows:
                indicator_scores[sr[0]] = sr[1]
            
            # ✅ 计算维度得分（百分制）
            # 优先使用教师调整后的 final_score，如果没有则使用 AI 原始分
            dimension_scores = {}
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                final_score = data.get(f"final_score_{key}")
                if final_score is not None and final_score > 0:
                    dimension_scores[key] = round(final_score, 2)
                else:
                    # 从指标重新计算
                    indicators = dim.get("sub_indicators", [])
                    if indicators:
                        dim_actual = 0
                        dim_max = 0
                        for ind in indicators:
                            ind_key = ind["key"]
                            dim_actual += indicator_scores.get(ind_key, 0)
                            dim_max += 10
                        if dim_max > 0:
                            dimension_scores[key] = round(dim_actual / dim_max * 100, 2)
                        else:
                            dimension_scores[key] = 0
                    else:
                        dimension_scores[key] = 0
            
            # ✅ 计算作业总分 = 所有指标得分直接相加
            total_score = sum(indicator_scores.values())
            
            # ✅ 如果教师有调整，优先使用教师调整后的总分
            if data.get("ai_comment") and "总分:" in data.get("ai_comment", ""):
                try:
                    comment = data.get("ai_comment", "")
                    if "总分:" in comment:
                        total_score = float(comment.split("总分:")[1].strip().split()[0])
                except:
                    pass
            
            # ✅ 获取测评报告（作为教师评语）
            evaluation_report = data.get("evaluation_report", None)
            # 如果 evaluation_report 是 JSON 字符串，尝试解析
            if evaluation_report and isinstance(evaluation_report, str):
                try:
                    evaluation_report = json.loads(evaluation_report)
                except:
                    pass
            
            data["indicator_scores"] = indicator_scores
            data["dimension_scores"] = dimension_scores
            data["total_score"] = round(total_score, 2)
            data["task_type"] = data.get("task_type", "任务实践")
            data["evaluation_report"] = evaluation_report  # ✅ 新增：测评报告
            results.append(data)
        
        return results
    except Exception as e:
        logger.error(f"获取已发布成绩失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()



def get_student_submissions_without_scores(student_username: str) -> List[Dict]:
    """
    获取学生未评分或未发布的提交记录
    """
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
        results = []
        
        for row in rows:
            data = dict(zip(columns, row))
            
            # 获取该提交的指标得分并计算总分
            cursor2 = conn.cursor()
            cursor2.execute("""
                SELECT score FROM submission_scores
                WHERE submission_id = ?
            """, (data["id"],))
            score_rows = cursor2.fetchall()
            
            # 计算总得分
            total_score = sum([sr[0] for sr in score_rows])
            data["total_score"] = round(total_score, 2) if total_score > 0 else None
            
            # 获取维度得分（优先使用 final_score）
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                final_score = data.get(f"final_score_{key}")
                ai_score = data.get(f"score_{key}")
                if final_score is not None and final_score > 0:
                    data[f"dimension_{key}"] = final_score
                else:
                    data[f"dimension_{key}"] = ai_score
            
            results.append(data)
        
        return results
    except Exception as e:
        logger.error(f"获取学生提交记录失败: {e}")
        return []
    finally:
        conn.close()


def get_submission_for_review(submission_id: int, include_scores: bool = True) -> Optional[Dict]:
    """
    获取提交详情（教师审批用）
    ✅ 返回时包含 final_score 和 score，前端可以显示对比
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
            # ✅ 计算加权总分（优先使用 final_score）
            total_score = 0
            total_weight = 0
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                weight = dim.get("weight", 0)
                # 优先用 final_score
                final_score = result.get(f"final_score_{key}")
                ai_score = result.get(f"score_{key}")
                score = final_score if final_score is not None and final_score > 0 else ai_score
                if score:
                    total_score += score * weight
                    total_weight += weight
            result["weighted_total"] = round(total_score / total_weight, 2) if total_weight > 0 else 0
        
        return result
    except Exception as e:
        logger.error(f"获取提交详情失败: {e}")
        return None
    finally:
        conn.close()


def get_all_submissions_summary() -> List[Dict]:
    """
    获取所有学生的提交汇总统计（管理员/教师用）
    ✅ 优先使用 final_score
    """
    db = SessionLocal()
    try:
        avg_columns = []
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            # 优先使用 final_score，如果没有则使用 score
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


def get_student_class_info(student_username: str) -> Optional[Dict]:
    """获取学生班级信息"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name 
            FROM user_class uc
            JOIN classes c ON uc.class_id = c.id
            JOIN users u ON u.id = uc.user_id
            WHERE u.username = ?
            LIMIT 1
        """, (student_username,))
        row = cursor.fetchone()
        if row:
            return {"class_id": row[0], "class_name": row[1]}
        return None
    except Exception as e:
        logger.error(f"获取学生班级信息失败: {e}")
        return None
    finally:
        conn.close()