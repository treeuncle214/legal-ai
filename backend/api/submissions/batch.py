"""
批量AI评分接口
"""
import asyncio
import json
import logging
from datetime import datetime
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user, get_teacher_class_ids
from backend.database import get_submissions_by_task_all
from backend.database.engine import SessionLocal
from backend.database.submissions import try_claim_scoring
from backend.database.tasks import get_task as get_task_db
from backend.api.submissions.scoring import perform_scoring

logger = logging.getLogger(__name__)
router = APIRouter()


def _save_batch_progress(task_id: int, data: dict):
    """将批量评分进度持久化到数据库（跨 worker 共享，修复多进程下进度丢失）"""
    db = SessionLocal()
    try:
        payload = json.dumps(data, ensure_ascii=False)
        updated_at = datetime.now().isoformat()
        row = db.execute(
            text("SELECT task_id FROM batch_progress WHERE task_id = :t"),
            {"t": task_id}
        ).fetchone()
        if row:
            db.execute(
                text("UPDATE batch_progress SET progress_data = :d, updated_at = :u WHERE task_id = :t"),
                {"t": task_id, "d": payload, "u": updated_at}
            )
        else:
            db.execute(
                text("INSERT INTO batch_progress (task_id, progress_data, updated_at) VALUES (:t, :d, :u)"),
                {"t": task_id, "d": payload, "u": updated_at}
            )
        db.commit()
    except Exception as e:
        logger.error(f"保存批量评分进度失败: {e}")
        db.rollback()
    finally:
        db.close()


def _load_batch_progress(task_id: int):
    """从数据库读取批量评分进度"""
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT progress_data FROM batch_progress WHERE task_id = :t"),
            {"t": task_id}
        ).fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        logger.error(f"读取批量评分进度失败: {e}")
    finally:
        db.close()
    return None


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

    progress = {
        "total": len(target_submissions),
        "completed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
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
    # 立即落库，让任意 worker 的轮询都能读到初始状态
    _save_batch_progress(task_id, progress)

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

    # 加载已持久化的进度（由 trigger 写入初始状态）
    progress = _load_batch_progress(task_id)
    if progress is None:
        progress = {
            "total": total,
            "completed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
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
                for sub in submissions
            ]
        }
        _save_batch_progress(task_id, progress)

    async def score_one(submission, index):
        username = submission.get("student_username")
        name = student_names.get(username, username)

        try:
            # 更新进度 - 当前处理
            progress["current_processing"] = f"{username}-{name}"
            progress["details"][index]["status"] = "scoring"
            _save_batch_progress(task_id, progress)

            if submission.get("ai_score_status") == "scoring":
                progress["details"][index]["status"] = "skipped"
                _save_batch_progress(task_id, progress)
                return {"submission_id": submission["id"], "status": "skipped", "reason": "评分中", "username": username, "name": name}

            if submission.get("ai_scored", False) and not force_retry:
                progress["details"][index]["status"] = "skipped"
                _save_batch_progress(task_id, progress)
                return {"submission_id": submission["id"], "status": "skipped", "reason": "已评分", "username": username, "name": name}

            content = submission.get("word_content", "")
            if not content:
                content = f"【AI交互记录】\n{submission.get('ai_interaction_log', '')}\n\n【作业正文】\n{submission.get('final_output', '')}"

            if not try_claim_scoring(submission["id"]):
                progress["details"][index]["status"] = "skipped"
                _save_batch_progress(task_id, progress)
                return {"submission_id": submission["id"], "status": "skipped", "reason": "评分中", "username": username, "name": name}

            async with semaphore:
                await asyncio.sleep(0.5)
                await perform_scoring(
                    submission_id=submission["id"],
                    task_dict=task_dict,
                    content=content,
                    submit_type=submission.get("submit_type", "word"),
                    teacher_username=teacher_username
                )

            progress["details"][index]["status"] = "success"
            _save_batch_progress(task_id, progress)
            return {"submission_id": submission["id"], "status": "success", "username": username, "name": name}

        except Exception as e:
            logger.error(f"批量评分 - 提交 {submission.get('id')} 失败: {e}")
            progress["details"][index]["status"] = "failed"
            _save_batch_progress(task_id, progress)
            return {"submission_id": submission.get("id"), "status": "failed", "error": str(e), "username": username, "name": name}

    # 并发执行所有评分任务（由 semaphore 限制并发数），每完成一个即更新进度与 ETA
    tasks = [asyncio.ensure_future(score_one(sub, idx)) for idx, sub in enumerate(submissions)]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        status = result.get("status") if isinstance(result, dict) else "failed"
        if status == "success":
            progress["success"] = progress.get("success", 0) + 1
        elif status == "failed":
            progress["failed"] = progress.get("failed", 0) + 1
        elif status == "skipped":
            progress["skipped"] = progress.get("skipped", 0) + 1

        progress["completed"] = progress.get("completed", 0) + 1
        elapsed = time.time() - progress.get("start_time", time.time())
        completed = progress["completed"]
        progress["elapsed_seconds"] = int(elapsed)
        # 预计剩余时间 = 平均单条耗时 × 剩余条数
        progress["estimated_remaining_seconds"] = int(elapsed / completed * (total - completed)) if completed > 0 else 0
        progress["current_processing"] = None
        _save_batch_progress(task_id, progress)

    # 完成
    progress["completed"] = total
    progress["current_processing"] = None
    progress["elapsed_seconds"] = int(time.time() - progress.get("start_time", time.time()))
    progress["estimated_remaining_seconds"] = 0
    progress["status"] = "completed" if progress.get("failed", 0) == 0 else "completed_with_errors"
    progress["completed_at"] = datetime.now().isoformat()
    _save_batch_progress(task_id, progress)

    logger.info(f"批量评分完成: 成功 {progress.get('success', 0)}, 失败 {progress.get('failed', 0)}, 跳过 {progress.get('skipped', 0)}")


@router.get("/submissions/batch-progress/{task_id}")
async def get_batch_progress(
    task_id: int,
    current_user: dict = Depends(get_current_user)
):
    """查询批次评分进度"""
    if current_user["role"] not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="只有教师可以查看")

    progress = _load_batch_progress(task_id)
    if progress is None:
        progress = {
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
        }
    return progress
