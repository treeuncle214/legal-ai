"""
查询接口
"""
import logging
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user, get_current_student, get_teacher_class_ids, get_student_class_id
from backend.database import get_submissions_by_student, get_task as get_task_db
from backend.database.submissions import get_submission, get_submission_count
from backend.database.models import SubmissionScore, TaskRubric, TaskRubricIndicator
from backend.database.engine import SessionLocal
from backend.config import SCORING_DIMENSIONS
from backend.schemas.common import Response as APIResponse
from backend.api.submissions.task_wrapper import TaskWrapper

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/submissions/{submission_id}/score")
async def get_submission_score(
    submission_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    if current_user["role"] not in ["teacher", "admin"] and submission["student_username"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权查看此提交")
    score_status = submission.get("ai_score_status", "pending")
    if score_status == "completed" and submission.get("ai_scored", False):
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
        return {"status": "pending", "message": "等待教师触发AI评分"}


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
    from backend.database import get_submissions_by_task_all
    
    task = get_task_db(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if current_user["role"] in ["teacher", "admin"]:
        teacher_class_ids = get_teacher_class_ids(current_user)
        if task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权查看此任务")
        submissions = get_submissions_by_task_all(task_id)
    else:
        student_class_id = get_student_class_id(current_user)
        if task.get("class_id") != student_class_id:
            raise HTTPException(status_code=403, detail="无权查看此任务")
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
        dimension_levels = {}
        for key, score in sub.get("dimension_scores", {}).items():
            if score >= 85:
                dimension_levels[key] = "优"
            elif score >= 75:
                dimension_levels[key] = "良"
            elif score >= 55:
                dimension_levels[key] = "合格"
            else:
                dimension_levels[key] = "不合格"
        
        # ✅ 获取测评报告（作为教师评语）
        evaluation_report = sub.get("evaluation_report", None)
        # 如果 evaluation_report 是 JSON 字符串，尝试解析
        if evaluation_report and isinstance(evaluation_report, str):
            try:
                evaluation_report = json.loads(evaluation_report)
            except:
                pass
        
        result.append({
            "id": sub["id"],
            "task_title": sub.get("task_title", "未知任务"),
            "task_type": sub.get("task_type", "任务实践"),
            "submit_time": sub.get("submit_time"),
            "total_score": sub.get("total_score", 0),
            "dimension_scores": sub.get("dimension_scores", {}),
            "dimension_levels": dimension_levels,
            "indicator_scores": sub.get("indicator_scores", {}),
            "teacher_comment": sub.get("teacher_comment", ""),
            "evaluation_report": evaluation_report,  # ✅ 新增：测评报告作为教师评语
            "is_reviewed": sub.get("is_reviewed", 1),
            "score_published": sub.get("score_published", 1)
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
    
    if current_user["role"] not in ["teacher", "admin"] and submission["student_username"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="无权查看此提交")
    
    if current_user["role"] in ["teacher", "admin"]:
        task = get_task_db(submission.get("task_id"))
        teacher_class_ids = get_teacher_class_ids(current_user)
        if task and task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权查看此提交")
    
    indicator_names = {}
    for dim in SCORING_DIMENSIONS:
        for ind in dim.get("sub_indicators", []):
            indicator_names[ind["key"]] = ind["name"]
    
    db_local = SessionLocal()
    try:
        scores = db_local.query(SubmissionScore).filter(
            SubmissionScore.submission_id == submission_id
        ).all()
        
        indicator_scores = {}
        indicator_levels = {}
        indicator_comments = {}
        indicator_max_scores = {}
        
        task_rubric = db_local.query(TaskRubric).filter(TaskRubric.task_id == submission.get("task_id")).first()
        if task_rubric:
            indicators = db_local.query(TaskRubricIndicator).filter(
                TaskRubricIndicator.task_rubric_id == task_rubric.id
            ).all()
            for ind in indicators:
                indicator_max_scores[ind.indicator_key] = ind.max_score
        
        valid_keys = ['A1','A2','A3','A4','B1','B2','B3','C1','C2','C3','D1','D2','D3']
        for s in scores:
            if s.indicator_key in valid_keys:
                indicator_scores[s.indicator_key] = s.score
                indicator_levels[s.indicator_key] = s.level
                indicator_comments[s.indicator_key] = s.comment
        
        submission["indicator_scores"] = indicator_scores
        submission["indicator_levels"] = indicator_levels
        submission["indicator_comments"] = indicator_comments
        submission["indicator_names"] = indicator_names
        submission["indicator_max_scores"] = indicator_max_scores
        
    finally:
        db_local.close()
    
    return APIResponse(data=submission)


@router.get("/submissions/remaining/{task_id}")
async def get_remaining_submissions(
    task_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    from backend.database import get_task
    task_dict = get_task(task_id)
    if not task_dict:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    student_class_id = get_student_class_id(current_user)
    if task_dict.get("class_id") != student_class_id:
        raise HTTPException(status_code=403, detail="无权查看此任务")
    
    task_obj = TaskWrapper(task_dict)
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


@router.get("/submissions/{submission_id}/ai-status")
async def get_submission_ai_status(
    submission_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个提交的AI评分状态"""
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    
    if current_user["role"] not in ["teacher", "admin"]:
        if submission["student_username"] != current_user["username"]:
            raise HTTPException(status_code=403, detail="无权查看")
    else:
        task = get_task_db(submission.get("task_id"))
        if task:
            teacher_class_ids = get_teacher_class_ids(current_user)
            if task.get("class_id") not in teacher_class_ids:
                raise HTTPException(status_code=403, detail="无权查看")
    
    return {
        "submission_id": submission_id,
        "ai_scored": submission.get("ai_scored", False),
        "ai_scored_at": submission.get("ai_scored_at"),
        "ai_scored_by": submission.get("ai_scored_by"),
        "ai_score_status": submission.get("ai_score_status", "pending"),
        "ai_score_error": submission.get("ai_score_error"),
        "has_content": bool(submission.get("word_file_path") or submission.get("final_output"))
    }