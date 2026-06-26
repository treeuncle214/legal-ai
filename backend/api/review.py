# backend/api/review.py
"""
教师审批 API
"""

from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
import logging
import json

from backend.api.deps import get_db, get_current_teacher
from backend.database import review_submission, get_submission
from backend.database.models import Submission
from backend.database.submissions import publish_submission_score
from backend.config import SCORING_DIMENSIONS
from backend.schemas.submission import ReviewRequest
from backend.schemas.common import Response
from fastapi import APIRouter, Depends, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["教师审批"])

# ==================== 请求模型 ====================
class PublishBatchRequest(BaseModel):
    task_id: int

    @validator('task_id')
    def task_id_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('task_id 必须为正整数')
        return v

# ==================== 批量发布接口（放在前面，避免路径冲突） ====================

@router.post("/review/publish_batch", response_model=Response)
async def publish_batch_scores(
    request: Request,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """批量发布某任务下所有已批改且未发布的成绩"""
    body = await request.body()
    print("原始请求体:", body)
    if not body:
        raise HTTPException(status_code=400, detail="请求体为空")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        print("JSON解析失败:", e)
        raise HTTPException(status_code=400, detail="无效的JSON格式")

    task_id = data.get("task_id")
    if task_id is None:
        raise HTTPException(status_code=400, detail="缺少 task_id")
    if not isinstance(task_id, int) or task_id <= 0:
        raise HTTPException(status_code=400, detail="task_id 必须为正整数")

    from backend.database.engine import get_db_connection
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE submissions 
            SET score_published = 1 
            WHERE task_id = ? AND is_reviewed = 1 AND (score_published IS NULL OR score_published = 0)
        """, (task_id,))
        conn.commit()
        count = cursor.rowcount
        return Response(data={"updated": count}, message=f"成功发布 {count} 份成绩")
    except Exception as e:
        logger.error(f"批量发布失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ==================== 现有接口 ====================

@router.post("/review/{submission_id}", response_model=Response)
async def review_submission_api(
    submission_id: int,
    review_data: ReviewRequest,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """教师审批并修改评分"""
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    
    review_submission(
        submission_id=submission_id,
        teacher_username=current_user["username"],
        scores_dict=review_data.scores,
        teacher_comment=review_data.teacher_comment
    )
    
    return Response(message="审批完成，评分已更新")


@router.post("/review/publish/{submission_id}", response_model=Response)
async def publish_score(
    submission_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """教师发布成绩：使该提交的分数和评语对学生可见"""
    from backend.database.submissions import get_submission_for_review
    
    submission = get_submission_for_review(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    
    if submission.get("is_reviewed") != 1:
        raise HTTPException(status_code=400, detail="请先完成审批再发布成绩")
    
    if submission.get("score_published") == 1:
        return Response(message="该成绩已发布，无需重复操作")
    
    success = publish_submission_score(submission_id)
    if not success:
        raise HTTPException(status_code=500, detail="发布失败，请重试")
    
    return Response(message="成绩已发布，学生端将可见")


@router.get("/review/pending", response_model=Response[list])
async def get_pending_reviews(
    current_user: dict = Depends(get_current_teacher),
):
    """获取所有待审批的提交（含发布状态）"""
    from backend.database import SessionLocal
    from backend.database.models import Submission
    from backend.config import SCORING_DIMENSIONS
    
    db = SessionLocal()
    try:
        pending_submissions = db.query(Submission).filter(
            Submission.is_reviewed == 0
        ).order_by(Submission.submit_time.desc()).all()
        
        result = []
        for sub in pending_submissions:
            task = sub.task
            scores_dict = {}
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                scores_dict[key] = getattr(sub, f"score_{key}", 0)
            
            result.append({
                "id": sub.id,
                "student_username": sub.student_username,
                "task_id": sub.task_id,
                "task_title": task.title if task else "未知任务",
                "submit_time": sub.submit_time.isoformat() if sub.submit_time else None,
                "is_reviewed": sub.is_reviewed,
                "score_published": sub.score_published or 0,
                "ai_comment": sub.ai_comment,
                "process_log": sub.process_log or "",
                "ai_interaction_log": sub.ai_interaction_log or "",
                "final_output": sub.final_output or "",
                "word_content": sub.word_content or "",
                "word_file_path": sub.word_file_path or "",
                "tools_used": sub.tools_used or "",
                "submit_type": sub.submit_type or "text",
                "scores": scores_dict,
            })
        
        return Response(data=result)
    finally:
        db.close()


# ==================== 按任务查看提交 ====================

@router.get("/review/task/{task_id}", response_model=Response[list])
async def get_task_reviews(
    task_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取某任务下所有学生的提交记录（含已审和待审）"""
    from backend.database import get_submissions_by_task
    submissions = get_submissions_by_task(task_id)
    return Response(data=submissions)