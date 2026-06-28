# backend/api/profile.py
"""
学生画像 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user, get_teacher_class_ids, get_student_class_id
from backend.database import calculate_profile, get_dimension_scores_history
from backend.database.tasks import get_task
from backend.schemas.common import Response

router = APIRouter(prefix="/api", tags=["学生画像"])


@router.get("/profile/{username}", response_model=Response)
async def get_profile(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取学生能力画像"""
    # 权限检查
    if current_user["role"] == "teacher":
        # 教师：验证该学生在自己班级
        from backend.database.engine import get_db_connection
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT uc.class_id 
                FROM user_class uc
                JOIN users u ON u.id = uc.user_id
                WHERE u.username = ?
            """, (username,))
            student_class_rows = cursor.fetchall()
            student_class_ids = [row[0] for row in student_class_rows]
            teacher_class_ids = get_teacher_class_ids(current_user)
            if not any(cid in teacher_class_ids for cid in student_class_ids):
                raise HTTPException(status_code=403, detail="无权查看该学生画像")
        finally:
            conn.close()
    elif current_user["username"] != username:
        raise HTTPException(status_code=403, detail="无权查看此画像")
    
    profile = calculate_profile(username)
    history = get_dimension_scores_history(username)
    
    return Response(
        data={
            "username": username,
            "display_name": current_user["display_name"] if current_user["username"] == username else None,
            "dimensions": profile["dimensions"],
            "overall_score": profile["overall"],
            "missing_dimensions": profile["missing_dimensions"],
            "history": history
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
    """获取学生的所有提交记录（教师可用）"""
    if current_user["role"] == "teacher":
        # 教师：验证该学生在自己班级
        from backend.database.engine import get_db_connection
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT uc.class_id 
                FROM user_class uc
                JOIN users u ON u.id = uc.user_id
                WHERE u.username = ?
            """, (username,))
            student_class_rows = cursor.fetchall()
            student_class_ids = [row[0] for row in student_class_rows]
            teacher_class_ids = get_teacher_class_ids(current_user)
            if not any(cid in teacher_class_ids for cid in student_class_ids):
                raise HTTPException(status_code=403, detail="无权查看该学生记录")
        finally:
            conn.close()
    elif current_user["username"] != username:
        raise HTTPException(status_code=403, detail="无权查看")
    
    from backend.database import get_submissions_by_student
    submissions = get_submissions_by_student(username)
    
    # 只返回必要字段
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