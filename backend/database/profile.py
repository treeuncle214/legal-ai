"""
学生画像计算函数
"""

from sqlalchemy import desc, func
from backend.database.engine import SessionLocal
from backend.database.models import Submission
from backend.config import SCORING_DIMENSIONS, get_dimension_name


def get_dimension_scores_history(student_username):
    """获取学生各维度的历史分数列表"""
    db = SessionLocal()
    try:
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username
        ).order_by(Submission.submit_time).all()
        
        result = {dim["key"]: [] for dim in SCORING_DIMENSIONS}
        
        for sub in submissions:
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                score = sub.get_dimension_score(key)
                if score > 0:
                    result[key].append(score)
        
        return result
    finally:
        db.close()


def calculate_profile(student_username, exercise_weight=0.6, final_weight=0.4):
    """
    计算学生能力画像 - 取每个维度的历史最高分
    """
    db = SessionLocal()
    try:
        # 查询该学生的所有提交
        all_submissions = db.query(Submission).filter(
            Submission.student_username == student_username
        ).all()

        if not all_submissions:
            return {
                "dimensions": {},
                "overall": 0,
                "missing_dimensions": [],
                "total_submissions": 0
            }

        # 初始化每个维度的最高分
        max_scores = {dim["key"]: 0.0 for dim in SCORING_DIMENSIONS}
        total_submissions = len(all_submissions)

        # 遍历所有提交，记录每个维度的最大值
        for sub in all_submissions:
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                score = sub.get_dimension_score(key)
                if score > max_scores[key]:
                    max_scores[key] = score

        # 构建结果
        result = {
            "dimensions": {},
            "overall": 0,
            "missing_dimensions": [],
            "total_submissions": total_submissions
        }

        weighted_total = 0.0
        total_weight = 0.0

        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            weight = dim.get("weight", 0.2)
            name = dim.get("name", key)
            max_score = max_scores[key]

            status = "evaluated" if max_score > 0 else "pending"
            if status == "pending":
                result["missing_dimensions"].append(key)

            result["dimensions"][key] = {
                "score": round(max_score, 2),
                "status": status,
                "name": name,
                "weight": weight,
                "exercise_avg": None,      # 不再使用平均分
                "final_avg": None,
                "submission_count": total_submissions
            }

            if status == "evaluated":
                weighted_total += max_score * weight
                total_weight += weight

        if total_weight > 0:
            result["overall"] = round(weighted_total / total_weight, 2)

        return result
    finally:
        db.close()
        
def get_student_profile(student_username):
    """
    获取学生能力画像数据（兼容旧版调用方式）
    返回：{"维度名": 分数, "完成任务数": n}
    """
    profile = calculate_profile(student_username)
    
    if profile["overall"] > 0 or any(d["status"] == "evaluated" for d in profile["dimensions"].values()):
        result = {}
        for key, dim_data in profile["dimensions"].items():
            if dim_data["status"] == "evaluated":
                result[dim_data["name"]] = dim_data["score"]
        
        # 获取完成任务数
        db = SessionLocal()
        try:
            task_count = db.query(Submission).filter(
                Submission.student_username == student_username
            ).count()
            result["完成任务数"] = task_count
        finally:
            db.close()
        
        return result
    
    return None