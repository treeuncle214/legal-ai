"""
AI评分触发接口
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user, get_teacher_class_ids
from backend.database.submissions import get_submission, try_claim_scoring
from backend.database.tasks import get_task as get_task_db
from backend.api.submissions.scoring import perform_scoring

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/submissions/{submission_id}/ai-score")
async def trigger_ai_score(
    submission_id: int,
    force_retry: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """触发单个提交的AI评分（教师控制）"""
    if current_user["role"] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师可以触发AI评分")
    
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    
    task = get_task_db(submission.get("task_id"))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此提交")
    
    if not submission.get("word_file_path") and not submission.get("final_output"):
        raise HTTPException(status_code=400, detail="该提交没有内容，无法评分")
    
    if submission.get("ai_scored", False) and not force_retry:
        raise HTTPException(status_code=400, detail="该提交已评分，如需重新评分请使用 force_retry=true")
    
    if submission.get("ai_score_status") == "scoring":
        raise HTTPException(status_code=409, detail="该提交正在评分中，请稍后")
    
    content = submission.get("word_content", "")
    if not content:
        content = f"【AI交互记录】\n{submission.get('ai_interaction_log', '')}\n\n【作业正文】\n{submission.get('final_output', '')}"
    
    if not try_claim_scoring(submission_id):
        raise HTTPException(status_code=409, detail="该提交正在评分中，请稍后")

    asyncio.create_task(
        perform_scoring(
            submission_id=submission_id,
            task_dict=task,
            content=content,
            submit_type=submission.get("submit_type", "word"),
            teacher_username=current_user["username"]
        )
    )
    
    return {
        "success": True,
        "submission_id": submission_id,
        "message": "AI评分已触发，请稍后刷新查看结果"
    }