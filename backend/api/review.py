# backend/api/review.py
"""
教师审批 API
"""

import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from backend.api.deps import get_db, get_current_teacher, get_teacher_class_ids
from backend.database import review_submission, get_submission
from backend.database.models import Submission
from backend.database.submissions import publish_submission_score
from backend.database.submissions import get_submissions_by_task_all
from backend.database.submissions.scoring import save_evaluation_report, get_evaluation_report
from backend.database.tasks import get_task as get_task_db
from backend.database.engine import SessionLocal
from backend.config import SCORING_DIMENSIONS
from backend.schemas.submission import ReviewRequest
from backend.schemas.common import Response
from backend.core.report_generator import generate_report
from backend.services.word_exporter import export_report_to_word

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


# ==================== 批量发布接口 ====================
@router.post("/review/publish_batch", response_model=Response)
async def publish_batch_scores(
    request: Request,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """批量发布某任务下所有已批改且未发布的成绩"""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="请求体为空")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="无效的JSON格式")

    task_id = data.get("task_id")
    if task_id is None:
        raise HTTPException(status_code=400, detail="缺少 task_id")
    if not isinstance(task_id, int) or task_id <= 0:
        raise HTTPException(status_code=400, detail="task_id 必须为正整数")
    
    # 验证任务属于当前教师
    task = get_task_db(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此任务")

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

 # ========== ✅ 调试日志 ==========
    print("=" * 60)
    print(f"🔍 review_submission_api 被调用")
    print(f"   submission_id: {submission_id}")
    print(f"   review_data.scores: {review_data.scores}")
    print(f"   review_data.indicator_scores: {review_data.indicator_scores}")
    print(f"   review_data.teacher_comment: {review_data.teacher_comment}")
    print("=" * 60)



    
    """教师审批并修改评分"""
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    
    # 验证提交对应的任务属于当前教师
    task = get_task_db(submission.get("task_id"))
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task and task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权审批此提交")
    
    review_submission(
        submission_id=submission_id,
        teacher_username=current_user["username"],
        scores_dict=review_data.scores,
        teacher_comment=review_data.teacher_comment,
        indicator_scores=review_data.indicator_scores
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
    
    # 验证提交对应的任务属于当前教师
    task = get_task_db(submission.get("task_id"))
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task and task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权发布此成绩")
    
    if submission.get("is_reviewed") != 1:
        raise HTTPException(status_code=400, detail="请先完成审批再发布成绩")
    
    if submission.get("score_published") == 1:
        return Response(message="该成绩已发布，无需重复操作")
    
    # ✅ 使用 SQLAlchemy 直接更新
    from backend.database.engine import SessionLocal
    from backend.database.models import Submission
    
    db_local = SessionLocal()
    try:
        submission_obj = db_local.query(Submission).filter(Submission.id == submission_id).first()
        if not submission_obj:
            raise HTTPException(status_code=404, detail="提交记录不存在")
        
        submission_obj.score_published = 1
        db_local.commit()
        
        logger.info(f"成绩发布成功: submission_id={submission_id}")
        return Response(message="成绩已发布，学生端将可见")
    except Exception as e:
        db_local.rollback()
        logger.error(f"发布成绩失败: {e}")
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")
    finally:
        db_local.close()

@router.get("/review/pending", response_model=Response[list])
async def get_pending_reviews(
    current_user: dict = Depends(get_current_teacher),
):
    """获取所有待审批的提交（仅当前教师班级）"""
    from backend.database.engine import get_db_connection
    from backend.database.tasks import get_task as get_task_db
    from backend.config import SCORING_DIMENSIONS
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if not teacher_class_ids:
        return Response(data=[])
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 查询每个学生每个任务的最新提交，且 is_reviewed = 0，且任务属于教师班级
        cursor.execute("""
            SELECT s.*, t.title as task_title
            FROM submissions s
            JOIN tasks t ON s.task_id = t.id
            WHERE s.id IN (
                SELECT MAX(id) 
                FROM submissions 
                WHERE is_reviewed = 0
                GROUP BY student_username, task_id
            )
            AND t.class_id IN ({})
            ORDER BY s.submit_time DESC
        """.format(','.join('?' * len(teacher_class_ids))), teacher_class_ids)
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        result = []
        for row in rows:
            sub = dict(zip(columns, row))
            scores_dict = {}
            for dim in SCORING_DIMENSIONS:
                key = dim["key"]
                scores_dict[key] = sub.get(f"score_{key}", 0)
            
            result.append({
                "id": sub["id"],
                "student_username": sub["student_username"],
                "task_id": sub["task_id"],
                "task_title": sub["task_title"],
                "submit_time": sub["submit_time"],
                "is_reviewed": sub["is_reviewed"],
                "score_published": sub.get("score_published", 0),
                "ai_comment": sub.get("ai_comment"),
                "process_log": sub.get("process_log", ""),
                "ai_interaction_log": sub.get("ai_interaction_log", ""),
                "final_output": sub.get("final_output", ""),
                "word_content": sub.get("word_content", ""),
                "word_file_path": sub.get("word_file_path", ""),
                "tools_used": sub.get("tools_used", ""),
                "submit_type": sub.get("submit_type", "text"),
                "scores": scores_dict,
            })
        
        return Response(data=result)
    except Exception as e:
        logger.error(f"获取待审批提交失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ==================== 按任务查看提交 ====================

@router.get("/review/task/{task_id}")
async def get_task_reviews(
    task_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取任务下每个学生的最新提交（用于审批评分）"""
    task = get_task_db(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此任务")
    
    from backend.database.engine import get_db_connection
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, t.title as task_title
            FROM submissions s
            JOIN tasks t ON s.task_id = t.id
            WHERE s.id IN (
                SELECT MAX(id)
                FROM submissions
                WHERE task_id = ?
                GROUP BY student_username
            )
            ORDER BY s.submit_time DESC
        """, (task_id,))
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        submissions = [dict(zip(columns, row)) for row in rows]
        
        # ✅ 为每个提交查询指标级评分和满分
        from backend.database.models import SubmissionScore, TaskRubricIndicator, TaskRubric
        from backend.database.engine import SessionLocal
        
        db_local = SessionLocal()
        try:
            # ✅ 查询该任务的所有指标满分
            rubric = db_local.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
            max_scores = {}
            if rubric:
                indicators = db_local.query(TaskRubricIndicator).filter(
                    TaskRubricIndicator.task_rubric_id == rubric.id
                ).all()
                for ind in indicators:
                    max_scores[ind.indicator_key] = ind.max_score
            
            for sub in submissions:
                scores = db_local.query(SubmissionScore).filter(
                    SubmissionScore.submission_id == sub["id"]
                ).all()
                
                indicator_scores = {}
                indicator_levels = {}
                indicator_comments = {}
                
                for s in scores:
                    valid_keys = ['A1','A2','A3','A4','B1','B2','B3','C1','C2','C3','D1','D2','D3']
                    if s.indicator_key in valid_keys:
                        indicator_scores[s.indicator_key] = s.score
                        indicator_levels[s.indicator_key] = s.level
                        indicator_comments[s.indicator_key] = s.comment
                
                sub["indicator_scores"] = indicator_scores
                sub["indicator_levels"] = indicator_levels
                sub["indicator_comments"] = indicator_comments
                sub["indicator_max_scores"] = max_scores
                
                # ✅ 新增：添加 final_score 字段（教师调整后的维度分数）
                final_scores = {}
                for dim in SCORING_DIMENSIONS:
                    key = dim["key"]
                    final_score = sub.get(f"final_score_{key}")
                    if final_score is not None and float(final_score) > 0:
                        final_scores[key] = float(final_score)
                    else:
                        # 如果没有调整分，使用 AI 原始分
                        final_scores[key] = sub.get(f"score_{key}", 0)
                sub["final_scores"] = final_scores
                
                # ✅ 新增：添加 final_score_xxx 字段到顶层（方便前端读取）
                for dim in SCORING_DIMENSIONS:
                    key = dim["key"]
                    sub[f"final_score_{key}"] = final_scores.get(key, 0)
        finally:
            db_local.close()
        
        return submissions
    finally:
        conn.close()
# ==================== 测评报告 API ====================

@router.get("/review/{submission_id}/report")
async def get_report(
    submission_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取测评报告"""
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    
    task = get_task_db(submission.get("task_id"))
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task and task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此报告")
    
    report = get_evaluation_report(submission_id)
    if not report:
        return {"success": True, "report": None, "message": "报告尚未生成"}
    
    return {"success": True, "report": report}

@router.post("/review/{submission_id}/generate-report")
async def generate_report_api(
    submission_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """生成测评报告"""
    from backend.database.engine import SessionLocal
    from backend.database.models import Submission, SubmissionScore, TaskRubric, TaskRubricIndicator
    
    db_local = SessionLocal()
    try:
        # ✅ 使用 SQLAlchemy 对象获取完整数据
        submission_obj = db_local.query(Submission).filter(Submission.id == submission_id).first()
        if not submission_obj:
            raise HTTPException(status_code=404, detail="提交记录不存在")
        
        task = get_task_db(submission_obj.task_id)
        teacher_class_ids = get_teacher_class_ids(current_user)
        if task and task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权操作此报告")
        
        # 获取指标得分
        scores = db_local.query(SubmissionScore).filter(
            SubmissionScore.submission_id == submission_id
        ).all()
        
        indicator_scores = {}
        for s in scores:
            if s.indicator_key in ['A1','A2','A3','A4','B1','B2','B3','C1','C2','C3','D1','D2','D3']:
                indicator_scores[s.indicator_key] = s.score
        
        # ✅ 从 SQLAlchemy 对象读取 final_score
        dimension_scores = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            final_score = getattr(submission_obj, f"final_score_{key}", None)
            ai_score = getattr(submission_obj, f"score_{key}", 0)
            
            if final_score is not None and float(final_score) > 0:
                dimension_scores[key] = float(final_score)
                logger.info(f"生成报告 维度 {key}: 使用教师调整分 {final_score}")
            else:
                dimension_scores[key] = float(ai_score)
                logger.info(f"生成报告 维度 {key}: 使用AI原始分 {ai_score}")
        
        # 获取模板提示词
        teacher_prompt = None
        indicator_details = None
        
        task_rubric = db_local.query(TaskRubric).filter(TaskRubric.task_id == task.get("id")).first()
        if task_rubric:
            teacher_prompt = task_rubric.overall_prompt
            
            indicators = db_local.query(TaskRubricIndicator).filter(
                TaskRubricIndicator.task_rubric_id == task_rubric.id
            ).all()
            if indicators:
                indicator_details = "评分指标详情：\n"
                for ind in indicators:
                    indicator_details += f"- {ind.indicator_key}: {ind.prompt or '（未设置详细描述）'}\n"
        
        # 获取学生内容和启用指标
        student_content = submission_obj.word_content or submission_obj.final_output or ""
        
        enabled_indicators = task.get("enabled_indicators", [])
        if isinstance(enabled_indicators, str):
            enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
        
    finally:
        db_local.close()
    
    # 生成报告
    report_data = generate_report(
        task_title=task.get("title", "法律检索任务"),
        task_type=task.get("task_type", "任务实践"),
        dimension_scores=dimension_scores,
        indicator_scores=indicator_scores,
        ai_comment=submission_obj.ai_comment if submission_obj else "",
        student_content=student_content,
        teacher_prompt=teacher_prompt,
        indicator_details=indicator_details,
        enabled_indicators=enabled_indicators
    )
    
    if not report_data:
        raise HTTPException(status_code=500, detail="报告生成失败")
    
    save_evaluation_report(submission_id, report_data)
    
    return {"success": True, "report": report_data, "message": "报告已生成"}

@router.post("/review/{submission_id}/save-report")
async def save_report_api(
    submission_id: int,
    request: Request,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """保存教师编辑后的测评报告"""
    submission = get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    
    task = get_task_db(submission.get("task_id"))
    teacher_class_ids = get_teacher_class_ids(current_user)
    if task and task.get("class_id") not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此报告")
    
    try:
        body = await request.body()
        data = json.loads(body)
    except:
        raise HTTPException(status_code=400, detail="无效的JSON数据")
    
    report_data = {
        "overall_evaluation": data.get("overall_evaluation", ""),
        "issue_feedback": data.get("issue_feedback", [])
    }
    
    save_evaluation_report(submission_id, report_data)
    
    return {"success": True, "message": "报告已保存"}


@router.get("/review/{submission_id}/download-report")
async def download_report(
    submission_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """下载Word格式的测评报告"""
    from backend.database.engine import SessionLocal
    from backend.database.models import Submission, SubmissionScore, TaskRubric, TaskRubricIndicator
    
    db_local = SessionLocal()
    try:
        submission_obj = db_local.query(Submission).filter(Submission.id == submission_id).first()
        if not submission_obj:
            raise HTTPException(status_code=404, detail="提交记录不存在")
        
        if submission_obj.is_reviewed != 1:
            raise HTTPException(
                status_code=400, 
                detail="请先完成审批（修改评分并保存），再生成测评报告。"
            )
        
        task = get_task_db(submission_obj.task_id)
        teacher_class_ids = get_teacher_class_ids(current_user)
        if task and task.get("class_id") not in teacher_class_ids:
            raise HTTPException(status_code=403, detail="无权下载此报告")
        
        report_data = get_evaluation_report(submission_id)
        if not report_data:
            raise HTTPException(status_code=404, detail="报告尚未生成，请先生成报告")
        
        # ========== 获取学生信息（含学院、专业） ==========
        student_username = submission_obj.student_username
        from backend.database.users import get_user
        user = get_user(student_username)
        student_name = user.get("display_name", student_username) if user else student_username
        student_college = user.get("college", "") if user else ""
        student_major = user.get("major", "") if user else ""
        
        # ========== 读取维度分数 ==========
        dimension_scores = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            final_score = getattr(submission_obj, f"final_score_{key}", None)
            ai_score = getattr(submission_obj, f"score_{key}", 0)
            
            if final_score is not None and float(final_score) > 0:
                dimension_scores[key] = float(final_score)
            else:
                dimension_scores[key] = float(ai_score)
        
        # ========== 读取指标得分 ==========
        indicator_scores = {}
        scores = db_local.query(SubmissionScore).filter(
            SubmissionScore.submission_id == submission_id
        ).all()
        for s in scores:
            if s.indicator_key in ['A1','A2','A3','A4','B1','B2','B3','C1','C2','C3','D1','D2','D3']:
                indicator_scores[s.indicator_key] = s.score
        
        # ========== 获取指标满分 ==========
        indicator_max_scores = {}
        task_rubric = db_local.query(TaskRubric).filter(TaskRubric.task_id == task.get("id")).first()
        if task_rubric:
            indicators = db_local.query(TaskRubricIndicator).filter(
                TaskRubricIndicator.task_rubric_id == task_rubric.id
            ).all()
            for ind in indicators:
                indicator_max_scores[ind.indicator_key] = ind.max_score
        
        report_data["indicator_max_scores"] = indicator_max_scores
        
        # ========== ✅ 生成Word文档 ==========
        file_path = export_report_to_word(
            student_name=student_name,
            student_id=student_username,
            task_title=task.get("title", "法律检索任务"),
            dimension_scores=dimension_scores,
            indicator_scores=indicator_scores,
            report_data=report_data,
            student_college=student_college,
            student_major=student_major,
            total_score=submission_obj.total_score  # ✅ 从数据库读取总分
        )
        
        if not file_path:
            raise HTTPException(status_code=500, detail="Word文档生成失败")
        
        filename = f"测评报告_{student_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    finally:
        db_local.close()