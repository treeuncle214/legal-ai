"""
学期总评 API
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from backend.api.deps import get_db, get_current_user, get_current_teacher, get_teacher_class_ids
from backend.database import get_class_students, get_user
from backend.database.engine import get_db_connection
from backend.database.models import Submission, Task, TermScore, SubmissionScore
from backend.config import SCORING_DIMENSIONS, get_level_by_score
from backend.schemas.common import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/term", tags=["学期总评"])


def calculate_term_score(student_username: str, class_id: int = None) -> Optional[dict]:
    """
    计算学生的学期总评
    
    公式：学期总成绩 = Σ(每次作业得分 × 该作业权重 / 100)
    作业得分 = 各指标得分直接相加（满分100分）
    """
    db = None
    try:
        from backend.database.engine import SessionLocal
        db = SessionLocal()
        
        # 获取该学生所有已发布的提交
        query = db.query(Submission).filter(
            Submission.student_username == student_username,
            Submission.score_published == 1,
            Submission.is_reviewed == 1
        )
        
        if class_id:
            query = query.join(Task).filter(Task.class_id == class_id)
        
        submissions = query.all()
        
        if not submissions:
            return None
        
        total_weighted = 0  # Σ(得分 × 权重)
        total_weight = 0    # Σ(权重)
        details = []
        
        for sub in submissions:
            task = db.query(Task).filter(Task.id == sub.task_id).first()
            if not task:
                continue
            
            weight = task.weight or 0
            
            # 计算该作业的得分（各指标直接相加）
            indicator_scores = db.query(SubmissionScore).filter(
                SubmissionScore.submission_id == sub.id
            ).all()
            
            total_score = sum([s.score for s in indicator_scores])
            
            # 计算加权贡献
            contribution = total_score * (weight / 100)
            total_weighted += contribution
            total_weight += weight
            
            details.append({
                "submission_id": sub.id,
                "task_id": task.id,
                "task_title": task.title,
                "task_type": task.task_type,
                "weight": weight,
                "score": round(total_score, 2),
                "contribution": round(contribution, 2)
            })
        
        if total_weight == 0:
            return None
        
        # 计算最终总评
        final_score = round(total_weighted / (total_weight / 100), 2)
        level = get_level_by_score(final_score)
        
        return {
            "student_username": student_username,
            "class_id": class_id,
            "total_score": final_score,
            "level": level,
            "submission_count": len(submissions),
            "total_weight": total_weight,
            "details": details
        }
        
    except Exception as e:
        logger.error(f"计算学期总评失败: {e}")
        return None
    finally:
        if db:
            db.close()


def save_term_score(student_username: str, term_data: dict):
    """保存学期总评到数据库"""
    db = None
    try:
        from backend.database.engine import SessionLocal
        db = SessionLocal()
        
        existing = db.query(TermScore).filter(
            TermScore.student_username == student_username,
            TermScore.class_id == term_data.get("class_id")
        ).first()
        
        if existing:
            existing.total_score = term_data["total_score"]
            existing.level = term_data["level"]
            existing.details = json.dumps(term_data.get("details", []), ensure_ascii=False)
            existing.updated_at = datetime.now()
        else:
            term_score = TermScore(
                student_username=student_username,
                class_id=term_data.get("class_id"),
                total_score=term_data["total_score"],
                level=term_data["level"],
                details=json.dumps(term_data.get("details", []), ensure_ascii=False),
                created_at=datetime.now()
            )
            db.add(term_score)
        
        db.commit()
        logger.info(f"学期总评已保存: {student_username}, 得分: {term_data['total_score']}")
    except Exception as e:
        logger.error(f"保存学期总评失败: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()


@router.get("/scores/{username}")
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
        teacher_class_ids = get_teacher_class_ids(current_user)
        if not teacher_class_ids:
            raise HTTPException(status_code=403, detail="您没有班级")
        
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
    
    term_score = db.query(TermScore).filter(
        TermScore.student_username == username
    ).first()
    
    if not term_score:
        # 尝试计算
        term_data = calculate_term_score(username)
        if term_data:
            save_term_score(username, term_data)
            term_score = db.query(TermScore).filter(
                TermScore.student_username == username
            ).first()
    
    if not term_score:
        return Response(data=None, message="暂无学期总评数据")
    
    return Response(data=term_score.to_dict())


@router.post("/scores/generate")
async def generate_term_scores_for_class(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """生成某个班级所有学生的学期总评"""
    teacher_class_ids = get_teacher_class_ids(current_user)
    if current_user["role"] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师可以生成学期总评")
    
    if current_user["role"] != "admin" and class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    students = get_class_students(class_id)
    if not students:
        return Response(message="该班级暂无学生")
    
    generated_count = 0
    errors = []
    
    for student in students:
        try:
            term_data = calculate_term_score(student["username"], class_id)
            if term_data:
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


@router.get("/scores/class/{class_id}")
async def get_class_term_scores(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取全班学生的学期总评列表"""
    teacher_class_ids = get_teacher_class_ids(current_user)
    if current_user["role"] != "admin" and class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此班级")
    
    term_scores = db.query(TermScore).filter(
        TermScore.class_id == class_id
    ).all()
    
    return Response(data=[ts.to_dict() for ts in term_scores])


@router.post("/scores/regenerate/{username}")
async def regenerate_student_term_score(
    username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """重新计算并更新单个学生的学期总评"""
    if current_user["role"] != "admin":
        teacher_class_ids = get_teacher_class_ids(current_user)
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
    
    # 获取学生的班级
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT uc.class_id 
            FROM user_class uc
            JOIN users u ON u.id = uc.user_id
            WHERE u.username = ?
        """, (username,))
        class_ids = [row[0] for row in cursor.fetchall()]
        class_id = class_ids[0] if class_ids else None
    finally:
        conn.close()
    
    term_data = calculate_term_score(username, class_id)
    if not term_data:
        raise HTTPException(status_code=404, detail="该学生没有足够的提交数据")
    
    save_term_score(username, term_data)
    
    return Response(data=term_data, message=f"{username} 的学期总评已更新")


@router.post("/scores/update-summary/{username}")
async def update_term_summary(
    username: str,
    summary: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """更新学期总评的教师总结"""
    term_score = db.query(TermScore).filter(
        TermScore.student_username == username
    ).first()
    
    if not term_score:
        raise HTTPException(status_code=404, detail="学期总评不存在")
    
    term_score.teacher_summary = summary
    db.commit()
    
    return Response(message="教师总结已更新")