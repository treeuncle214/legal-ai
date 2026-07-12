# backend/api/term_scores.py
"""
学期总评 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.api.deps import get_db, get_current_user, get_current_teacher, get_teacher_class_ids
from backend.database.term_scores import (
    calculate_term_score, 
    save_term_score, 
    get_term_score,
    get_all_term_scores
)
from backend.database import get_user, get_class_students
from backend.schemas.common import Response

router = APIRouter(prefix="/api/term", tags=["学期总评"])


@router.get("/scores/{username}", response_model=Response)
async def get_student_term_score(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取学生的学期总评
    - 学生只能查看自己的
    - 教师只能查看自己班级学生的
    - admin 可以查看所有
    """
    # 权限校验
    if current_user["role"] == "student":
        if current_user["username"] != username:
            raise HTTPException(status_code=403, detail="无权查看其他学生的学期总评")
    elif current_user["role"] == "teacher":
        # 验证该学生在教师班级中
        teacher_class_ids = get_teacher_class_ids(current_user)
        if not teacher_class_ids:
            raise HTTPException(status_code=403, detail="您没有班级")
        
        # 获取该学生的班级
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
            student_classes = [row[0] for row in cursor.fetchall()]
            
            if not any(cid in teacher_class_ids for cid in student_classes):
                raise HTTPException(status_code=403, detail="该学生不在您班级中")
        finally:
            conn.close()
    # admin 可以查看所有，不做限制
    
    # 获取学期总评
    term_score = get_term_score(username)
    if not term_score:
        return Response(data=None, message="暂无学期总评数据")
    
    return Response(data=term_score)


@router.post("/scores/generate", response_model=Response)
async def generate_term_scores_for_class(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    生成某个班级所有学生的学期总评
    """
    # 验证班级属于当前教师
    teacher_class_ids = get_teacher_class_ids(current_user)
    if current_user["username"] != "admin" and class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    # 获取班级所有学生
    students = get_class_students(class_id)
    if not students:
        return Response(message="该班级暂无学生")
    
    # 为每个学生计算并保存学期总评
    generated_count = 0
    errors = []
    
    for student in students:
        try:
            # 计算学期总评
            term_data = calculate_term_score(student["username"])
            if term_data:
                # 保存到数据库
                save_term_score(student["username"], term_data)
                generated_count += 1
        except Exception as e:
            errors.append(f"{student['username']}: {str(e)}")
    
    message = f"成功生成 {generated_count} 名学生的学期总评"
    if errors:
        message += f"，失败 {len(errors)} 名"
    
    return Response(
        data={"generated": generated_count, "errors": errors},
        message=message
    )


@router.get("/scores/class/{class_id}", response_model=Response[list])
async def get_class_term_scores(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    获取全班学生的学期总评列表（教师端）
    """
    # 验证班级属于当前教师
    teacher_class_ids = get_teacher_class_ids(current_user)
    if current_user["username"] != "admin" and class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此班级")
    
    # 获取班级所有学生的学期总评
    term_scores = get_all_term_scores(class_id)
    
    return Response(data=term_scores)


@router.post("/scores/regenerate/{username}", response_model=Response)
async def regenerate_student_term_score(
    username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    重新计算并更新单个学生的学期总评
    """
    # 验证该学生在教师班级中
    if current_user["username"] != "admin":
        teacher_class_ids = get_teacher_class_ids(current_user)
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
            student_classes = [row[0] for row in cursor.fetchall()]
            if not any(cid in teacher_class_ids for cid in student_classes):
                raise HTTPException(status_code=403, detail="该学生不在您班级中")
        finally:
            conn.close()
    
    # 重新计算
    term_data = calculate_term_score(username)
    if not term_data:
        raise HTTPException(status_code=404, detail="该学生没有足够的提交数据")
    
    save_term_score(username, term_data)
    
    return Response(data=term_data, message=f"{username} 的学期总评已更新")