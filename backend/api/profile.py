"""
学生画像 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any

from backend.api.deps import get_db, get_current_user, get_teacher_class_ids, get_student_class_id
from backend.database import calculate_profile, get_dimension_scores_history
from backend.database.tasks import get_task
from backend.database.classes import get_class_students, get_class
from backend.database.engine import SessionLocal
from backend.database.models import User
from backend.schemas.common import Response
from backend.config import SCORING_DIMENSIONS
from backend.database.submissions import get_published_submissions_for_student

router = APIRouter(prefix="/api", tags=["学生画像"])


def _check_teacher_access_to_student(username: str, current_user: dict) -> None:
    """检查教师是否有权访问该学生"""
    db_session = SessionLocal()
    try:
        result = db_session.execute(text("""
            SELECT uc.class_id 
            FROM user_class uc
            JOIN users u ON u.id = uc.user_id
            WHERE u.username = :username
        """), {"username": username})
        student_class_ids = [row[0] for row in result.fetchall()]
        teacher_class_ids = get_teacher_class_ids(current_user)
        if not any(cid in teacher_class_ids for cid in student_class_ids):
            raise HTTPException(status_code=403, detail="无权查看该学生画像")
    finally:
        db_session.close()


@router.get("/profile/{username}", response_model=Response)
async def get_profile(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生能力画像"""
    if current_user["role"] == "teacher":
        _check_teacher_access_to_student(username, current_user)
    elif current_user["username"] != username:
        raise HTTPException(status_code=403, detail="无权查看此画像")

    student_user = db.query(User).filter(User.username == username).first()
    if not student_user:
        raise HTTPException(status_code=404, detail="学生不存在")

    profile = calculate_profile(username)
    history = get_dimension_scores_history(username)

    from backend.database.classes import get_student_class_info
    class_info = get_student_class_info(username)

    return Response(
        data={
            "username": username,
            "display_name": student_user.display_name or username,
            "college": student_user.college or "",
            "major": student_user.major or "",
            "ai_retrieval": profile.get("ai_retrieval", 0),
            "critical": profile.get("critical", 0),
            "ethics": profile.get("ethics", 0),
            "integration": profile.get("integration", 0),
            "overall": profile.get("overall", 0),
            "overall_level": profile.get("overall_level", "待评测"),
            "total_submissions": profile.get("total_submissions", 0),
            "exercise_count": profile.get("exercise_count", 0),
            "practice_count": profile.get("practice_count", 0),
            "final_count": profile.get("final_count", 0),
            "dimensions": profile.get("dimensions", {}),
            "history": history,
            "class_id": class_info.get("class_id") if class_info else None,
            "class_name": class_info.get("class_name") if class_info else None
        }
    )


@router.get("/dimensions", response_model=Response)
async def get_dimensions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取评分维度配置"""
    from backend.config import SCORING_DIMENSIONS, INDICATORS

    return Response(
        data={
            "dimensions": SCORING_DIMENSIONS,
            "indicators": INDICATORS
        }
    )


@router.get("/profile/{username}/submissions")
async def get_student_submissions_history(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生的所有提交记录"""
    if current_user["role"] == "teacher":
        _check_teacher_access_to_student(username, current_user)
    elif current_user["username"] != username:
        raise HTTPException(status_code=403, detail="无权查看")

    from backend.database import get_submissions_by_student
    submissions = get_submissions_by_student(username)

    result = []
    for sub in submissions:
        result.append({
            "id": sub["id"],
            "task_title": sub.get("task_title"),
            "submit_time": sub.get("submit_time"),
            "submit_type": sub.get("submit_type"),
            "is_reviewed": sub.get("is_reviewed"),
            "weighted_total": sub.get("weighted_total"),
            "scores": sub.get("scores", {})
        })

    return Response(data=result)


@router.get("/class-rank/{username}")
async def get_student_class_rank(
    username: str,
    class_id: int = Query(..., description="班级ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取学生在班级中的排名"""
    student = db.query(User).filter(User.username == username, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    class_info = get_class(class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="班级不存在")

    class_name = class_info.get("name", f"班级{class_id}")

    if current_user["role"] == "student" and current_user["username"] != username:
        raise HTTPException(status_code=403, detail="无权查看其他学生的班级排名")

    if current_user["role"] == "teacher":
        _check_teacher_access_to_student(username, current_user)

    class_students = get_class_students(class_id)
    student_usernames = [s["username"] for s in class_students]

    if username not in student_usernames:
        raise HTTPException(status_code=400, detail="该学生不在本班级中")

    student_scores = get_published_submissions_for_student(username)

    if not student_scores:
        return {
            "username": username,
            "display_name": student.display_name or username,
            "class_id": class_id,
            "class_name": class_name,
            "dimensions": {},
            "total_students": len(student_usernames),
            "message": "该生暂无已发布的成绩"
        }

    student_dim_avg = {}
    for dim in SCORING_DIMENSIONS:
        key = dim["key"]
        scores = [s.get("dimension_scores", {}).get(key, 0) for s in student_scores if s.get("dimension_scores", {}).get(key, 0) > 0]
        student_dim_avg[key] = round(sum(scores) / len(scores), 2) if scores else 0

    class_dim_scores = {key: [] for key in student_dim_avg.keys()}

    for other_username in student_usernames:
        if other_username == username:
            continue
        other_scores = get_published_submissions_for_student(other_username)
        if other_scores:
            other_dim_avg = {}
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                scores = [s.get("dimension_scores", {}).get(key, 0) for s in other_scores if s.get("dimension_scores", {}).get(key, 0) > 0]
                other_dim_avg[key] = round(sum(scores) / len(scores), 2) if scores else 0
            for key in other_dim_avg.keys():
                if other_dim_avg[key] > 0:
                    class_dim_scores[key].append(other_dim_avg[key])

    result_dimensions = {}
    for dim in SCORING_DIMENSIONS:
        key = dim["key"]
        if student_dim_avg.get(key, 0) == 0:
            continue

        all_scores = class_dim_scores.get(key, [])
        class_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

        all_scores_with_student = all_scores + [student_dim_avg[key]]
        sorted_scores = sorted(all_scores_with_student, reverse=True)
        rank = sorted_scores.index(student_dim_avg[key]) + 1

        percentile = round((1 - (rank - 1) / len(student_usernames)) * 100, 1)

        result_dimensions[key] = {
            "name": dim["name"],
            "score": student_dim_avg[key],
            "class_avg": class_avg,
            "rank": rank,
            "total_students": len(student_usernames),
            "percentile": percentile
        }

    return {
        "username": username,
        "display_name": student.display_name or username,
        "class_id": class_id,
        "class_name": class_name,
        "dimensions": result_dimensions,
        "total_students": len(student_usernames)
    }