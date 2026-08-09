"""
学生画像计算函数
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy import desc, func
from backend.database.engine import SessionLocal
from backend.database.models import Submission, SubmissionScore, Task,User, Class, UserClass
from backend.config import SCORING_DIMENSIONS, get_dimension_name

logger = logging.getLogger(__name__)


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
                if score is not None and score > 0:
                    result[key].append(score)
        
        return result
    except Exception as e:
        logger.error(f"获取维度历史分数失败: {e}")
        return {dim["key"]: [] for dim in SCORING_DIMENSIONS}
    finally:
        db.close()

def calculate_profile(student_username: str) -> Dict:
    """
    计算学生能力画像
    ✅ 改为直接平均分（不区分作业类型，不除以权重）
    """
    db = SessionLocal()
    try:
        # ✅ 获取用户信息（含学院、专业）
        user = db.query(User).filter(User.username == student_username).first()
        if not user:
            return None
        
        # ✅ 获取班级信息
        class_info = db.query(UserClass).filter(UserClass.user_id == user.id).first()
        class_name = None
        class_id = None
        if class_info:
            cls = db.query(Class).filter(Class.id == class_info.class_id).first()
            if cls:
                class_name = cls.name
                class_id = cls.id
        
        # 1. 获取所有已发布的提交
        submissions = db.query(Submission).filter(
            Submission.student_username == student_username,
            Submission.score_published == 1,
            Submission.is_reviewed == 1
        ).all()
        
        if not submissions:
            return {
                "username": user.username,
                "display_name": user.display_name or user.username,
                "college": user.college or "",
                "major": user.major or "",
                "class_name": class_name,
                "class_id": class_id,
                "ai_retrieval": 0,
                "critical": 0,
                "ethics": 0,
                "integration": 0,
                "overall": 0,
                "overall_level": "待评测",
                "total_submissions": 0,
                "exercise_count": 0,
                "practice_count": 0,
                "final_count": 0,
                "dimensions": {}
            }
        
        # 2. 获取每个提交的指标得分
        submission_ids = [s.id for s in submissions]
        indicator_scores = db.query(SubmissionScore).filter(
            SubmissionScore.submission_id.in_(submission_ids)
        ).all()
        
        # 按提交分组
        scores_by_submission = {}
        for score in indicator_scores:
            if score.submission_id not in scores_by_submission:
                scores_by_submission[score.submission_id] = {}
            scores_by_submission[score.submission_id][score.indicator_key] = score.score
        
        # 3. 统计任务类型（仅用于展示）
        task_type_count = {"课堂练习": 0, "任务实践": 0, "综合考察": 0}
        for sub in submissions:
            task = db.query(Task).filter(Task.id == sub.task_id).first()
            task_type = task.task_type if task else "任务实践"
            if task_type in task_type_count:
                task_type_count[task_type] += 1
        
        # 4. ✅ 计算每个维度的平均分（直接平均，不区分类型）
        dim_all_scores = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            dim_all_scores[key] = []
        
        for sub in submissions:
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                sub_indicators = dim.get("sub_indicators", [])
                if sub_indicators:
                    total_score = 0
                    total_max = 0
                    for ind in sub_indicators:
                        ind_key = ind["key"]
                        max_score = 10
                        total_max += max_score
                        total_score += scores_by_submission.get(sub.id, {}).get(ind_key, 0)
                    if total_max > 0:
                        dim_score = total_score / total_max * 100
                        if dim_score > 0:
                            dim_all_scores[key].append(dim_score)
        
        # 直接平均
        dim_avg = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            scores = dim_all_scores.get(key, [])
            dim_avg[key] = round(sum(scores) / len(scores), 2) if scores else 0
        
        # 5. ✅ 计算每个提交的总成绩（作业总分 = 指标直接相加，满分100分）
        submission_overall_scores = []
        for sub in submissions:
            total = 0
            for dim in SCORING_DIMENSIONS:
                sub_indicators = dim.get("sub_indicators", [])
                for ind in sub_indicators:
                    ind_key = ind["key"]
                    total += scores_by_submission.get(sub.id, {}).get(ind_key, 0)
            if total > 0:
                submission_overall_scores.append(round(total, 2))
        
        overall = round(sum(submission_overall_scores) / len(submission_overall_scores), 2) if submission_overall_scores else 0
        
        # 6. 计算综合等级
        overall_level = get_level(overall)
        
        # 7. 构建各维度详情
        dimensions = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            score = dim_avg.get(key, 0)
            level = get_level(score)
            status = "evaluated" if score > 0 else "pending"
            
            indicator_scores_detail = {}
            for sub in submissions:
                for ind in dim.get("sub_indicators", []):
                    ind_key = ind["key"]
                    if ind_key not in indicator_scores_detail:
                        indicator_scores_detail[ind_key] = []
                    score_val = scores_by_submission.get(sub.id, {}).get(ind_key, 0)
                    if score_val > 0:
                        indicator_scores_detail[ind_key].append(score_val)
            
            indicator_avg = {}
            for ind_key, scores_list in indicator_scores_detail.items():
                if scores_list:
                    indicator_avg[ind_key] = round(sum(scores_list) / len(scores_list), 2)
            
            dimensions[key] = {
                "score": score,
                "level": level,
                "status": status,
                "indicator_scores": indicator_avg
            }
        
        # ✅ 返回包含用户信息的完整数据
        return {
            "username": user.username,
            "display_name": user.display_name or user.username,
            "college": user.college or "",
            "major": user.major or "",
            "class_name": class_name,
            "class_id": class_id,
            "ai_retrieval": dim_avg.get("ai_retrieval", 0),
            "critical": dim_avg.get("critical", 0),
            "ethics": dim_avg.get("ethics", 0),
            "integration": dim_avg.get("integration", 0),
            "overall": overall,
            "overall_level": overall_level,
            "total_submissions": len(submissions),
            "exercise_count": task_type_count.get("课堂练习", 0),
            "practice_count": task_type_count.get("任务实践", 0),
            "final_count": task_type_count.get("综合考察", 0),
            "dimensions": dimensions
        }
        
    except Exception as e:
        logger.error(f"计算能力画像失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ai_retrieval": 0,
            "critical": 0,
            "ethics": 0,
            "integration": 0,
            "overall": 0,
            "overall_level": "待评测",
            "total_submissions": 0,
            "exercise_count": 0,
            "practice_count": 0,
            "final_count": 0,
            "dimensions": {}
        }
    finally:
        db.close()

def get_level(score: float) -> str:
    """根据得分获取等级"""
    if score >= 85:
        return "优秀"
    elif score >= 75:
        return "良好"
    elif score >= 55:
        return "合格"
    else:
        return "不合格"


def get_student_profile(student_username: str):
    """
    获取学生能力画像数据（兼容旧版调用方式）
    """
    profile = calculate_profile(student_username)
    
    if profile.get("total_submissions", 0) > 0 or profile.get("overall", 0) > 0:
        result = {}
        dim_name_map = {
            "ai_retrieval": "AI融合智能检索能力",
            "critical": "批判性评估能力",
            "ethics": "伦理合规辨识能力",
            "integration": "信息整合应用能力"
        }
        for key, name in dim_name_map.items():
            if profile.get(key, 0) > 0:
                result[name] = profile[key]
        
        result["完成任务数"] = profile.get("total_submissions", 0)
        result["总成绩"] = profile.get("overall", 0)
        result["class_id"] = profile.get("class_id")
        result["class_name"] = profile.get("class_name")
        
        return result
    
    return None