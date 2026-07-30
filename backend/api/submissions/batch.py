"""
批量AI评分接口
"""
import asyncio
import logging
from datetime import datetime
import time

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
    
    # 获取学生姓名映射
    from backend.database.models import User
    from backend.database.engine import SessionLocal
    db_local = SessionLocal()
    try:
        student_names = {}
        for sub in all_submissions:
            username = sub.get("student_username")
            if username and username not in student_names:
                user = db_local.query(User).filter(User.username == username).first()
                student_names[username] = user.display_name if user else username
    finally:
        db_local.close()
    
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
        "start_time": time.time(),
        "current_processing": None,
        "details": [
            {
                "username": sub.get("student_username"),
                "name": student_names.get(sub.get("student_username"), sub.get("student_username")),
                "status": "pending"
            }
            for sub in target_submissions
        ]
    }
    
    semaphore = asyncio.Semaphore(min(concurrent_limit, 5))
    
    asyncio.create_task(
        process_batch_scoring(
            submissions=target_submissions,
            task_dict=task,
            teacher_username=current_user["username"],
            force_retry=force_retry,
            semaphore=semaphore,
            task_id=task_id,
            student_names=student_names
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
    task_id: int,
    student_names: dict
):
    """后台批量评分任务"""
    total = len(submissions)
    
    async def score_one(submission, index):
        username = submission.get("student_username")
        name = student_names.get(username, username)
        
        try:
            # 更新进度 - 当前处理
            _batch_progress_cache[task_id]["current_processing"] = f"{username}-{name}"
            _batch_progress_cache[task_id]["details"][index]["status"] = "scoring"
            
            if submission.get("ai_score_status") == "scoring":
                _batch_progress_cache[task_id]["details"][index]["status"] = "skipped"
                return {"submission_id": submission["id"], "status": "skipped", "reason": "评分中", "username": username, "name": name}
            
            if submission.get("ai_scored", False) and not force_retry:
                _batch_progress_cache[task_id]["details"][index]["status"] = "skipped"
                return {"submission_id": submission["id"], "status": "skipped", "reason": "已评分", "username": username, "name": name}
            
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
            
            _batch_progress_cache[task_id]["details"][index]["status"] = "success"
            return {"submission_id": submission["id"], "status": "success", "username": username, "name": name}
            
        except Exception as e:
            logger.error(f"批量评分 - 提交 {submission.get('id')} 失败: {e}")
            _batch_progress_cache[task_id]["details"][index]["status"] = "failed"
            return {"submission_id": submission.get("id"), "status": "failed", "error": str(e), "username": username, "name": name}
    
    # 创建所有任务
    tasks = [score_one(sub, idx) for idx, sub in enumerate(submissions)]
    
    # 逐个执行并更新进度
    for idx, task in enumerate(tasks):
        result = await task
        # 更新进度缓存
        cache = _batch_progress_cache.get(task_id, {})
        if result.get("status") == "success":
            cache["success"] = cache.get("success", 0) + 1
        elif result.get("status") == "failed":
            cache["failed"] = cache.get("failed", 0) + 1
        elif result.get("status") == "skipped":
            cache["skipped"] = cache.get("skipped", 0) + 1
        cache["completed"] = idx + 1
        cache["current_processing"] = None
        
        # 计算预计剩余时间
        elapsed = time.time() - cache.get("start_time", time.time())
        if idx + 1 > 0:
            avg_time_per_item = elapsed / (idx + 1)
            remaining = total - (idx + 1)
            cache["estimated_remaining_seconds"] = int(avg_time_per_item * remaining)
            cache["elapsed_seconds"] = int(elapsed)
        
        _batch_progress_cache[task_id] = cache
    
    # 完成
    cache = _batch_progress_cache.get(task_id, {})
    cache["status"] = "completed" if cache.get("failed", 0) == 0 else "completed_with_errors"
    cache["completed_at"] = datetime.now().isoformat()
    cache["current_processing"] = None
    cache["estimated_remaining_seconds"] = 0
    _batch_progress_cache[task_id] = cache
    
    logger.info(f"批量评分完成: 成功 {cache.get('success', 0)}, 失败 {cache.get('failed', 0)}, 跳过 {cache.get('skipped', 0)}")


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
        "message": "没有进行中的批量评分任务",
        "estimated_remaining_seconds": 0,
        "elapsed_seconds": 0,
        "current_processing": None,
        "details": []
    })
    return progress