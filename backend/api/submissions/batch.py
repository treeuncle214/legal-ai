"""
批量AI评分接口
"""
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user, get_teacher_class_ids
from backend.database import get_submissions_by_task_all
from backend.database.submissions import update_ai_score_status
from backend.database.tasks import get_task as get_task_db
from backend.api.submissions.scoring import perform_scoring

logger = logging.getLogger(__name__)
router = APIRouter()

# 批次评分进度缓存
_batch_progress_cache = {}


@router.post("/submissions/batch-ai-score")
async def trigger_batch_ai_score(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量触发AI评分（教师控制）"""
    if current_user["role"] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师可以触发AI评分")
    
    task_id = request.get("task_id")
    student_usernames = request.get("student_usernames")
    force_retry = request.get("force_retry", False)
    concurrent_limit = request.get("concurrent_limit", 3)
    
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id 是必填参数")
    
    task = get_task_db(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    all_submissions = get_submissions_by_task_all(task_id)
    
    target_submissions = []
    for sub in all_submissions:
        if not sub.get("word_file_path") and not sub.get("final_output"):
            continue
        if student_usernames and sub.get("student_username") not in student_usernames:
            continue
        if sub.get("ai_scored", False) and not force_retry:
            continue
        if sub.get("ai_score_status") == "scoring":
            continue
        target_submissions.append(sub)
    
    if not target_submissions:
        return {
            "success": True,
            "task_id": task_id,
            "total": 0,
            "message": "没有需要评分的提交"
        }
    
    _batch_progress_cache[task_id] = {
        "total": len(target_submissions),
        "completed": 0,
        "success": 0,
        "failed": 0,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "details": []
    }
    
    semaphore = asyncio.Semaphore(min(concurrent_limit, 5))
    
    asyncio.create_task(
        process_batch_scoring(
            submissions=target_submissions,
            task_dict=task,
            teacher_username=current_user["username"],
            force_retry=force_retry,
            semaphore=semaphore,
            task_id=task_id
        )
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "total": len(target_submissions),
        "message": f"已启动批次评分，共 {len(target_submissions)} 人，并发数: {concurrent_limit}"
    }


async def process_batch_scoring(
    submissions: list,
    task_dict: dict,
    teacher_username: str,
    force_retry: bool,
    semaphore: asyncio.Semaphore,
    task_id: int
):
    """后台批量评分任务"""
    async def score_one(submission):
        try:
            if submission.get("ai_score_status") == "scoring":
                return {"submission_id": submission["id"], "status": "skipped", "reason": "评分中"}
            if submission.get("ai_scored", False) and not force_retry:
                return {"submission_id": submission["id"], "status": "skipped", "reason": "已评分"}
            
            content = submission.get("word_content", "")
            if not content:
                content = f"【AI交互记录】\n{submission.get('ai_interaction_log', '')}\n\n【作业正文】\n{submission.get('final_output', '')}"
            
            update_ai_score_status(submission["id"], "scoring")
            
            async with semaphore:
                await asyncio.sleep(0.5)
                await perform_scoring(
                    submission_id=submission["id"],
                    task_dict=task_dict,
                    content=content,
                    submit_type=submission.get("submit_type", "word"),
                    teacher_username=teacher_username
                )
            
            return {"submission_id": submission["id"], "status": "success"}
        except Exception as e:
            logger.error(f"批量评分 - 提交 {submission.get('id')} 失败: {e}")
            return {"submission_id": submission.get("id"), "status": "failed", "error": str(e)}
    
    tasks = [score_one(sub) for sub in submissions]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    details = []
    
    for result in results:
        if isinstance(result, Exception):
            failed_count += 1
            details.append({"status": "error", "error": str(result)})
        elif isinstance(result, dict):
            if result.get("status") == "success":
                success_count += 1
            elif result.get("status") == "failed":
                failed_count += 1
            else:
                skipped_count += 1
            details.append(result)
        else:
            failed_count += 1
    
    _batch_progress_cache[task_id] = {
        "total": len(submissions),
        "completed": success_count + failed_count,
        "success": success_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "status": "completed" if failed_count == 0 else "completed_with_errors",
        "completed_at": datetime.now().isoformat(),
        "details": details
    }
    
    logger.info(f"批量评分完成: 成功 {success_count}, 失败 {failed_count}, 跳过 {skipped_count}")


@router.get("/submissions/batch-progress/{task_id}")
async def get_batch_progress(
    task_id: int,
    current_user: dict = Depends(get_current_user)
):
    """查询批次评分进度"""
    if current_user["role"] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师可以查看")
    
    progress = _batch_progress_cache.get(task_id, {
        "total": 0,
        "completed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "status": "idle",
        "message": "没有进行中的批量评分任务"
    })
    return progress