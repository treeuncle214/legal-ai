"""
班级学情分析逻辑
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.database.models import User, Class, Task, Submission, SubmissionScore
from backend.database.classes import get_class_students, get_class
from backend.config import SCORING_DIMENSIONS
from backend.api.scores.helpers import get_level, get_indicator_max_score


def get_class_analytics_data(
    class_id: int,
    task_type: Optional[str],
    db: Session,
    current_user: dict
) -> Dict:
    """
    获取班级学情分析数据
    """
    # 1. 验证班级和权限
    class_info = get_class(class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    # class_info 是字典，用 .get() 访问
    class_name = class_info.get("name", f"班级{class_id}")
    
    # 2. 获取班级学生
    students = get_class_students(class_id)
    student_usernames = [s["username"] for s in students]
    
    if not student_usernames:
        return {
            "class_id": class_id,
            "class_name": class_name,
            "students": [],
            "dimension_avg": {},
            "indicator_avg": {},
            "level_distribution": {},
            "task_trends": [],
            "total_students": 0,
            "total_tasks": 0
        }
    
    # 3. 获取班级任务
    tasks = db.query(Task).filter(
        Task.class_id == class_id,
        Task.is_active == 1
    )
    if task_type:
        tasks = tasks.filter(Task.task_type == task_type)
    tasks = tasks.order_by(Task.created_at).all()
    
    if not tasks:
        return {
            "class_id": class_id,
            "class_name": class_name,
            "students": [],
            "dimension_avg": {},
            "indicator_avg": {},
            "level_distribution": {},
            "task_trends": [],
            "total_students": len(student_usernames),
            "total_tasks": 0
        }
    
    # 4. 收集所有学生的已发布成绩
    all_published_scores = []
    student_score_map = {s: [] for s in student_usernames}
    
    for task in tasks:
        submissions = db.query(Submission).filter(
            Submission.task_id == task.id,
            Submission.student_username.in_(student_usernames),
            Submission.score_published == 1,
            Submission.is_reviewed == 1
        ).all()
        
        for sub in submissions:
            indicator_scores = db.query(SubmissionScore).filter(
                SubmissionScore.submission_id == sub.id
            ).all()
            
            indicator_dict = {s.indicator_key: s.score for s in indicator_scores}
            
            # 计算维度得分
            dimension_scores = {}
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                sub_indicators = dim.get("sub_indicators", [])
                if sub_indicators:
                    total_score = 0
                    total_max = 0
                    for ind in sub_indicators:
                        ind_key = ind["key"]
                        max_score = get_indicator_max_score(task.id, ind_key, db)
                        if max_score:
                            total_max += max_score
                            total_score += indicator_dict.get(ind_key, 0)
                    if total_max > 0:
                        dimension_scores[key] = round(total_score / total_max * 100, 2)
                    else:
                        dimension_scores[key] = 0
                else:
                    dimension_scores[key] = 0
            
            total = sum(indicator_dict.values())
            
            all_published_scores.append({
                "student_username": sub.student_username,
                "task_id": task.id,
                "task_title": task.title,
                "task_type": task.task_type,
                "task_created_at": task.created_at,
                "total_score": round(total, 2),
                "dimension_scores": dimension_scores,
                "indicator_scores": indicator_dict
            })
            
            student_score_map[sub.student_username].append({
                "task_id": task.id,
                "task_title": task.title,
                "task_type": task.task_type,
                "total_score": round(total, 2),
                "dimension_scores": dimension_scores,
                "indicator_scores": indicator_dict
            })
    
    # 5. 计算各维度平均分
    dimension_avg = {}
    for dim in SCORING_DIMENSIONS:
        key = dim["key"]
        scores = [s["dimension_scores"].get(key, 0) for s in all_published_scores if s["dimension_scores"].get(key, 0) > 0]
        dimension_avg[key] = {
            "name": dim["name"],
            "average": round(sum(scores) / len(scores), 2) if scores else 0,
            "count": len(scores)
        }
    
    # 6. 计算各指标平均分
    indicator_avg = {}
    for dim in SCORING_DIMENSIONS:
        for ind in dim.get("sub_indicators", []):
            key = ind["key"]
            scores = [s["indicator_scores"].get(key, 0) for s in all_published_scores if key in s["indicator_scores"]]
            indicator_avg[key] = {
                "name": ind["name"],
                "dimension": dim["key"],
                "dimension_name": dim["name"],
                "average": round(sum(scores) / len(scores), 2) if scores else 0,
                "count": len(scores)
            }
    
    # 7. 等级分布
    level_distribution = {"优秀": 0, "良好": 0, "合格": 0, "不合格": 0, "未提交": 0}
    for student_username in student_usernames:
        student_scores = student_score_map.get(student_username, [])
        if not student_scores:
            level_distribution["未提交"] += 1
            continue
        avg_score = sum([s["total_score"] for s in student_scores]) / len(student_scores)
        level = get_level(avg_score)
        level_distribution[level] = level_distribution.get(level, 0) + 1
    
    # 8. 任务趋势
    task_trends = []
    for task in tasks:
        task_scores = [s for s in all_published_scores if s["task_id"] == task.id]
        if not task_scores:
            continue
        dim_avg = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            scores = [s["dimension_scores"].get(key, 0) for s in task_scores if s["dimension_scores"].get(key, 0) > 0]
            dim_avg[key] = round(sum(scores) / len(scores), 2) if scores else 0
        task_trends.append({
            "task_id": task.id,
            "task_title": task.title,
            "task_type": task.task_type,
            "created_at": task.created_at.strftime("%Y-%m-%d") if task.created_at else "",
            "dimension_scores": dim_avg,
            "total_avg": round(sum([s["total_score"] for s in task_scores]) / len(task_scores), 2)
        })
    
    # 9. 学生详情
    student_details = []
    for student_username in student_usernames:
        student = db.query(User).filter(User.username == student_username).first()
        scores = student_score_map.get(student_username, [])
        if scores:
            avg_score = sum([s["total_score"] for s in scores]) / len(scores)
            level = get_level(avg_score)
        else:
            avg_score = 0
            level = "未提交"
        student_details.append({
            "username": student_username,
            "display_name": student.display_name if student else student_username,
            "average_score": round(avg_score, 2),
            "level": level,
            "submission_count": len(scores),
            "scores": scores
        })
    
    return {
        "class_id": class_id,
        "class_name": class_name,
        "teacher_name": current_user.get("display_name", ""),
        "students": student_details,
        "dimension_avg": dimension_avg,
        "indicator_avg": indicator_avg,
        "level_distribution": level_distribution,
        "task_trends": task_trends,
        "total_students": len(student_usernames),
        "total_tasks": len(tasks)
    }