"""
学期总评 CRUD 操作
"""

from sqlalchemy.orm import Session
from backend.database.engine import SessionLocal
from backend.database.models import TermScore, Submission, Task
from backend.config import SCORING_DIMENSIONS
from typing import Dict, List, Optional
from datetime import datetime
from backend.database.models import User


def calculate_term_score(student_username: str) -> Dict:
    """
    计算学生的学期综合成绩
    返回各维度得分、二级指标得分、课程总成绩
    """
    db = SessionLocal()
    try:
        # 获取该学生的所有已批改提交
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username,
            Submission.is_reviewed == 1
        ).all()

        if not submissions:
            return None

        # 按任务类型分组
        exercise_scores = {}   # 课堂练习
        practice_scores = {}   # 任务实践
        final_scores = {}      # 综合考察

        for sub in submissions:
            task = db.query(Task).filter(Task.id == sub.task_id).first()
            if not task:
                continue

            task_type = task.task_type or "课堂练习"
            scores = sub.get_scores_dict()  # 获取4个维度得分

            if task_type == "课堂练习":
                exercise_scores[sub.id] = scores
            elif task_type == "任务实践":
                practice_scores[sub.id] = scores
            elif task_type == "综合考察":
                final_scores[sub.id] = scores

        # 计算各类型各维度的平均分
        def calc_avg(scores_list, dim_key):
            if not scores_list:
                return None
            valid = [s.get(dim_key, 0) for s in scores_list if s.get(dim_key) is not None]
            return sum(valid) / len(valid) if valid else None

        result = {
            "student_username": student_username,
            "exercise_count": len(exercise_scores),
            "practice_count": len(practice_scores),
            "final_count": len(final_scores),
            "dimension_scores": {},
            "indicator_scores": {},
            "course_total_score": 0
        }

        # 计算各维度综合得分
        weights = {"课堂练习": 0.20, "任务实践": 0.40, "综合考察": 0.40}

        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            ex_avg = calc_avg(list(exercise_scores.values()), key)
            pr_avg = calc_avg(list(practice_scores.values()), key)
            fn_avg = calc_avg(list(final_scores.values()), key)

            # 加权计算
            weighted_sum = 0
            total_weight = 0

            if ex_avg is not None:
                weighted_sum += ex_avg * 0.20
                total_weight += 0.20
            if pr_avg is not None:
                weighted_sum += pr_avg * 0.40
                total_weight += 0.40
            if fn_avg is not None:
                weighted_sum += fn_avg * 0.40
                total_weight += 0.40

            if total_weight > 0:
                result["dimension_scores"][key] = weighted_sum / total_weight
            else:
                result["dimension_scores"][key] = 0

        # 计算各二级指标综合得分（类似逻辑，按指标维度计算）
        # ...（简化，实际使用时需要遍历每个二级指标）

        # 计算课程总成绩
        total = 0
        for sub in submissions:
            task = db.query(Task).filter(Task.id == sub.task_id).first()
            if task and task.weight:
                total += sub.calculate_weighted_total() * (task.weight / 100)
        result["course_total_score"] = round(total, 2)

        return result
    finally:
        db.close()


def save_term_score(student_username: str, data: Dict) -> int:
    """保存学期总评快照"""
    db = SessionLocal()
    try:
        # 删除旧的记录
        db.query(TermScore).filter(TermScore.student_username == student_username).delete()

        term_score = TermScore(
            student_username=student_username,
            course_total_score=data.get("course_total_score", 0),
            A_ai_retrieval_score=data.get("dimension_scores", {}).get("ai_retrieval"),
            B_critical_score=data.get("dimension_scores", {}).get("critical"),
            C_ethics_score=data.get("dimension_scores", {}).get("ethics"),
            D_integration_score=data.get("dimension_scores", {}).get("integration"),
            exercise_count=data.get("exercise_count", 0),
            practice_count=data.get("practice_count", 0),
            final_count=data.get("final_count", 0)
        )
        db.add(term_score)
        db.commit()
        db.refresh(term_score)
        return term_score.id
    finally:
        db.close()


def get_term_score(student_username: str) -> Optional[Dict]:
    """获取学生的学期总评"""
    db = SessionLocal()
    try:
        term_score = db.query(TermScore).filter(
            TermScore.student_username == student_username
        ).first()
        return term_score.to_dict() if term_score else None
    finally:
        db.close()


def get_all_term_scores(class_id: int = None) -> List[Dict]:
    """获取全班学期总评"""
    db = SessionLocal()
    try:
        query = db.query(TermScore)
        if class_id:
            # 只返回该班级的学生
            from backend.database.models import UserClass, User
            subquery = db.query(UserClass.user_id).filter(
                UserClass.class_id == class_id
            ).subquery()
            query = query.filter(TermScore.student_username.in_(
                db.query(User.username).filter(User.id.in_(subquery))
            ))
        
        results = query.all()
        return [r.to_dict() for r in results]
    finally:
        db.close()