"""
提交复杂查询
"""

from typing import List, Dict, Optional
import logging
import json

from sqlalchemy import func
from backend.database.engine import SessionLocal
from backend.database.models import Submission, SubmissionScore, User, Task
from backend.config import SCORING_DIMENSIONS, get_level_by_score

logger = logging.getLogger(__name__)


def get_published_submissions_for_student(student_username: str) -> List[Dict]:
    """获取学生所有已发布的成绩"""
    db = SessionLocal()
    try:
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username,
            Submission.score_published == 1,
            Submission.is_reviewed == 1
        ).order_by(Submission.submit_time.desc()).all()

        results = []
        for s in submissions:
            task = db.query(Task).filter(Task.id == s.task_id).first()

            data = {c.name: getattr(s, c.name) for c in s.__table__.columns}
            data["task_title"] = task.title if task else None
            data["task_type"] = task.task_type if task else "任务实践"

            scores = db.query(SubmissionScore).filter(
                SubmissionScore.submission_id == s.id
            ).all()
            indicator_scores = {sc.indicator_key: sc.score for sc in scores}

            dimension_scores = {}
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                final_score = getattr(s, f"final_score_{key}", None)
                if final_score is not None and final_score > 0:
                    dimension_scores[key] = round(final_score, 2)
                else:
                    indicators = dim.get("sub_indicators", [])
                    if indicators:
                        dim_actual = sum(indicator_scores.get(ind["key"], 0) for ind in indicators)
                        dim_max = len(indicators) * 10
                        dimension_scores[key] = round(dim_actual / dim_max * 100, 2) if dim_max > 0 else 0
                    else:
                        dimension_scores[key] = 0

            total_score = sum(indicator_scores.values())

            evaluation_report = getattr(s, "evaluation_report", None)
            if evaluation_report and isinstance(evaluation_report, str):
                try:
                    evaluation_report = json.loads(evaluation_report)
                except:
                    pass

            data["indicator_scores"] = indicator_scores
            data["dimension_scores"] = dimension_scores
            data["total_score"] = round(total_score, 2)
            data["evaluation_report"] = evaluation_report
            results.append(data)

        return results
    except Exception as e:
        logger.error(f"获取已发布成绩失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        db.close()


def get_student_submissions_without_scores(student_username: str) -> List[Dict]:
    """获取学生未评分或未发布的提交记录"""
    db = SessionLocal()
    try:
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username
        ).order_by(Submission.submit_time.desc()).all()

        results = []
        for s in submissions:
            task = db.query(Task).filter(Task.id == s.task_id).first()
            data = {c.name: getattr(s, c.name) for c in s.__table__.columns}
            data["task_title"] = task.title if task else None

            scores = db.query(SubmissionScore).filter(
                SubmissionScore.submission_id == s.id
            ).all()
            total_score = sum(sc.score for sc in scores)
            data["total_score"] = round(total_score, 2) if total_score > 0 else None

            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                final_score = getattr(s, f"final_score_{key}", None)
                ai_score = getattr(s, f"score_{key}", None)
                data[f"dimension_{key}"] = final_score if final_score is not None and final_score > 0 else ai_score

            results.append(data)

        return results
    except Exception as e:
        logger.error(f"获取学生提交记录失败: {e}")
        return []
    finally:
        db.close()


def get_submission_for_review(submission_id: int, include_scores: bool = True) -> Optional[Dict]:
    """获取提交详情（教师审批用）"""
    db = SessionLocal()
    try:
        s = db.query(Submission).filter(Submission.id == submission_id).first()
        if not s:
            return None

        result = {c.name: getattr(s, c.name) for c in s.__table__.columns}

        if include_scores:
            total_score = 0
            total_weight = 0
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                weight = dim.get("weight", 0)
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
        db.close()


def get_all_submissions_summary() -> List[Dict]:
    """获取所有学生的提交汇总统计"""
    db = SessionLocal()
    try:
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


def get_student_class_info(student_username: str) -> Optional[Dict]:
    """获取学生班级信息"""
    db = SessionLocal()
    try:
        from backend.database.models import UserClass, Class
        user = db.query(User).filter(User.username == student_username).first()
        if not user:
            return None

        uc = db.query(UserClass).filter(UserClass.user_id == user.id).first()
        if not uc:
            return None

        cls = db.query(Class).filter(Class.id == uc.class_id).first()
        if cls:
            return {"class_id": cls.id, "class_name": cls.name}
        return None
    except Exception as e:
        logger.error(f"获取学生班级信息失败: {e}")
        return None
    finally:
        db.close()