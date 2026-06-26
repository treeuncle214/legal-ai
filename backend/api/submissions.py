# backend/api/submissions.py
"""
提交和评分 API
"""

import os
import tempfile
import shutil
import uuid
import asyncio
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from fastapi.responses import FileResponse
import logging
from docx import Document

from backend.api.deps import get_db, get_current_user, get_current_student
from backend.database import (
    add_submission, update_scores, get_task, get_submissions_by_student
)
from backend.database.submissions import (
    can_submit, get_submission_count, get_submission, update_ai_score_status,
    delete_submission  # 保留以备其他用途
)
from backend.core.scorer import score_submission
from backend.schemas.submission import TextSubmissionRequest
from backend.schemas.common import Response as APIResponse
from backend.config import UPLOAD_DIR

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024
router = APIRouter(prefix="/api", tags=["提交评分"])


class TaskWrapper:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.title = data.get('title')
        self.description = data.get('description')
        self.due_date = data.get('due_date')
        self.task_type = data.get('task_type', '任务实践')
        self.enabled_indicators = data.get('enabled_indicators', '')
        self.max_submissions = data.get('max_submissions', 3)
        self.allow_after_deadline = data.get('allow_after_deadline', 0)
    
    def get_enabled_indicators_list(self) -> List[str]:
        if not self.enabled_indicators:
            return []
        return [s.strip() for s in self.enabled_indicators.split(',') if s.strip()]


# ========== OPTIONS 处理 ==========
@router.options("/submissions/text")
async def options_submissions_text():
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    })

@router.options("/submissions/word")
async def options_submissions_word():
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    })


# ========== AI 评分异步任务 ==========
async def perform_scoring(submission_id: int, task_dict: dict, content: str, submit_type: str):
    try:
        logger.info(f"开始为提交 {submission_id} 进行AI评分")
        update_ai_score_status(submission_id, "scoring")
        score_result = score_submission(task_dict, {"final_output": content, "submit_type": submit_type})
        scores_dict = {
            "score_ai_retrieval": score_result["dimension_scores"].get("ai_retrieval", 0),
            "score_critical": score_result["dimension_scores"].get("critical", 0),
            "score_ethics": score_result["dimension_scores"].get("ethics", 0),
            "score_integration": score_result["dimension_scores"].get("integration", 0),
            "ai_comment": score_result.get("comment", "AI评分完成"),
            "ai_score_status": "completed",
            "ai_score_detail": score_result.get("indicator_grades", {}) if "indicator_grades" in score_result else score_result.get("module_scores", {})
        }
        update_scores(submission_id, scores_dict)
        logger.info(f"提交 {submission_id} AI评分完成")
    except Exception as e:
        logger.error(f"提交 {submission_id} AI评分失败: {str(e)}", exc_info=True)
        # 不再删除记录，改为标记失败，供教师手动处理
        update_ai_score_status(submission_id, "failed", error_message=str(e))
        update_scores(submission_id, {"ai_comment": "AI评分失败，请教师手动批改", "ai_score_status": "failed"})


# ========== 文本提交（保留，但前端已不再使用） ==========
@router.post("/submissions/text", response_model=APIResponse)
async def submit_text(
    submission_data: TextSubmissionRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    try:
        task_dict = get_task(submission_data.task_id)
        if not task_dict:
            raise HTTPException(status_code=404, detail="任务不存在")
        task_obj = TaskWrapper(task_dict)
        can_sub, check_message = can_submit(current_user["username"], submission_data.task_id, task_obj)
        if not can_sub:
            raise HTTPException(status_code=400, detail=check_message)
        content = submission_data.final_output
        score_result = score_submission(task_dict, {"final_output": content, "submit_type": "text"})
        submission_id = add_submission(
            task_id=submission_data.task_id,
            student_username=current_user["username"],
            process_log=submission_data.process_log,
            ai_interaction_log=submission_data.ai_interaction_log,
            final_output=content,
            tools_used=",".join(submission_data.tools_used) if submission_data.tools_used else "",
            submit_type="text",
            ai_score_status="completed"
        )
        scores_dict = {
            "score_ai_retrieval": score_result["dimension_scores"].get("ai_retrieval", 0),
            "score_critical": score_result["dimension_scores"].get("critical", 0),
            "score_ethics": score_result["dimension_scores"].get("ethics", 0),
            "score_integration": score_result["dimension_scores"].get("integration", 0),
            "ai_comment": score_result.get("comment", "AI评分完成"),
            "ai_score_detail": str(score_result.get("indicator_grades", {})) if "indicator_grades" in score_result else str(score_result.get("module_scores", {}))
        }
        update_scores(submission_id, scores_dict)
        submission_count = get_submission_count(current_user["username"], submission_data.task_id)
        remaining_after = max(0, task_obj.max_submissions - submission_count)
        return APIResponse(
            data={
                "submission_id": submission_id,
                "status": "completed",
                "dimension_scores": score_result["dimension_scores"],
                "ai_comment": score_result.get("comment", ""),
                "remaining_submissions": remaining_after,
                "max_submissions": task_obj.max_submissions,
                "submitted_count": submission_count
            },
            message=f"提交成功！剩余提交次数：{remaining_after}"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ========== Word 双文件提交 ==========
@router.post("/submissions/word", response_model=APIResponse)
async def submit_word(
    task_id: int = Form(...),
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """上传两个Word文档：file1=检索过程，file2=最终结果"""
    # 校验文件
    for f in [file1, file2]:
        f.file.seek(0, 2)
        if f.file.tell() > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"文件 {f.filename} 超过大小限制")
        f.file.seek(0)
        if not f.filename.lower().endswith('.docx'):
            raise HTTPException(status_code=400, detail=f"{f.filename} 不是 .docx 格式")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 读取并提取文本
    try:
        content1 = await file1.read()
        content2 = await file2.read()
        doc1 = Document(io.BytesIO(content1))
        doc2 = Document(io.BytesIO(content2))
        process_log_text = "\n".join([p.text for p in doc1.paragraphs]).strip()
        final_output_text = "\n".join([p.text for p in doc2.paragraphs]).strip()
        if not process_log_text or not final_output_text:
            raise HTTPException(status_code=400, detail="两个文档内容均不能为空")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析文档失败: {str(e)}")

    # 获取任务
    task_dict = get_task(task_id)
    if not task_dict:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_obj = TaskWrapper(task_dict)

    # 检查提交次数
    can_sub, check_message = can_submit(current_user["username"], task_id, task_obj)
    if not can_sub:
        raise HTTPException(status_code=400, detail=check_message)

    # 保存文件
    unique1 = f"{uuid.uuid4().hex}.docx"
    unique2 = f"{uuid.uuid4().hex}.docx"
    path1 = os.path.join(UPLOAD_DIR, unique1)
    path2 = os.path.join(UPLOAD_DIR, unique2)
    with open(path1, "wb") as f:
        f.write(content1)
    with open(path2, "wb") as f:
        f.write(content2)

    # 合并内容给AI
    combined = f"【检索过程记录】\n{process_log_text}\n\n【最终检索结果】\n{final_output_text}"

    # 插入数据库，状态 pending
    submission_id = add_submission(
        task_id=task_id,
        student_username=current_user["username"],
        process_log=process_log_text,
        final_output=final_output_text,
        submit_type="word",
        word_file_path=f"{unique1},{unique2}",   # 两个文件名逗号分隔
        word_content=combined,
        ai_score_status="pending"
    )

    # 异步执行AI评分
    asyncio.create_task(
        perform_scoring(
            submission_id=submission_id,
            task_dict=task_dict,
            content=combined,
            submit_type="word"
        )
    )

    # 返回成功（不含评分）
    return APIResponse(
        data={"submission_id": submission_id, "message": "提交成功，等待教师批改"},
        message="提交成功！请等待教师批改后查看成绩"
    )


# ========== 其余查询接口（保持原有功能） ==========
@router.get("/submissions/{submission_id}/score")
async def get_submission_score(
    submission_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    if current_user["role"] != "teacher" and submission["student_username"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权查看此提交")
    score_status = submission.get("ai_score_status", "pending")
    if score_status == "completed":
        return {
            "status": "completed",
            "data": {
                "dimension_scores": {
                    "ai_retrieval": submission.get("score_ai_retrieval", 0),
                    "critical": submission.get("score_critical", 0),
                    "ethics": submission.get("score_ethics", 0),
                    "integration": submission.get("score_integration", 0)
                },
                "ai_comment": submission.get("ai_comment", ""),
                "ai_score_detail": submission.get("ai_score_detail", {})
            }
        }
    elif score_status == "scoring":
        return {"status": "scoring", "message": "AI评分进行中，请稍后"}
    elif score_status == "failed":
        return {"status": "failed", "message": f"AI评分失败: {submission.get('ai_score_error', '未知错误')}"}
    else:
        return {"status": "pending", "message": "等待评分开始"}


@router.get("/submissions/student/{username}", response_model=APIResponse[list])
async def get_student_submissions(
    username: str,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    if current_user["username"] != username:
        raise HTTPException(status_code=403, detail="只能查看自己的提交记录")
    from backend.database.submissions import get_student_submissions_without_scores
    submissions = get_student_submissions_without_scores(username)
    return APIResponse(data=submissions)


@router.get("/submissions/task/{task_id}", response_model=APIResponse[list])
async def get_task_submissions(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from backend.database import get_submissions_by_task
    if current_user["role"] == "teacher":
        submissions = get_submissions_by_task(task_id)
    else:
        submissions = get_submissions_by_student(current_user["username"])
        submissions = [s for s in submissions if s["task_id"] == task_id]
    return APIResponse(data=submissions)


@router.get("/submissions/published", response_model=APIResponse[list])
async def get_published_scores(
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    from backend.database.submissions import get_published_submissions_for_student
    submissions = get_published_submissions_for_student(current_user["username"])
    result = []
    for sub in submissions:
        result.append({
            "id": sub["id"],
            "task_title": sub.get("task_title", "未知任务"),
            "weighted_total": sub.get("weighted_total", 0),
            "teacher_comment": sub.get("teacher_comment", ""),
            "submit_time": sub.get("submit_time"),
            "is_reviewed": sub.get("is_reviewed", 1),
        })
    return APIResponse(data=result)


@router.get("/submissions/{submission_id}", response_model=APIResponse)
async def get_submission_detail(
    submission_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    if current_user["role"] != "teacher" and submission["student_username"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权查看此提交")
    return APIResponse(data=submission)


@router.get("/submissions/remaining/{task_id}")
async def get_remaining_submissions(
    task_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    task_dict = get_task(task_id)
    if not task_dict:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_obj = TaskWrapper(task_dict)
    # 使用新的统计函数（统计所有记录）
    from backend.database.submissions import get_submission_count
    submission_count = get_submission_count(current_user["username"], task_id)
    remaining = max(0, task_obj.max_submissions - submission_count)
    is_deadline_passed = False
    if task_obj.due_date and not task_obj.allow_after_deadline:
        try:
            due_date = datetime.fromisoformat(task_obj.due_date) if isinstance(task_obj.due_date, str) else task_obj.due_date
            is_deadline_passed = datetime.now() > due_date
        except:
            pass
    return {
        "remaining": remaining,
        "max_submissions": task_obj.max_submissions,
        "submitted_count": submission_count,
        "is_deadline_passed": is_deadline_passed,
        "due_date": task_obj.due_date,
        "allow_after_deadline": task_obj.allow_after_deadline == 1
    }


@router.get("/download/{filename}")
async def download_file(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    if '..' in filename or filename.startswith('/'):
        raise HTTPException(status_code=400, detail="无效的文件名")
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )