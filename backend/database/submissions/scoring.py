"""
提交评分相关操作
"""
import json
import logging
from datetime import datetime
from typing import Optional

from backend.database.engine import SessionLocal
from backend.database.models import Submission, SubmissionScore

logger = logging.getLogger(__name__)

def update_scores(submission_id: int, scores: dict):
    """更新提交的评分数据"""
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"提交 {submission_id} 不存在")
            return
        
        if "score_ai_retrieval" in scores:
            submission.score_ai_retrieval = scores["score_ai_retrieval"]
        if "score_critical" in scores:
            submission.score_critical = scores["score_critical"]
        if "score_ethics" in scores:
            submission.score_ethics = scores["score_ethics"]
        if "score_integration" in scores:
            submission.score_integration = scores["score_integration"]
        
        # ✅ 新增：保存总分
        if "total_score" in scores:
            submission.total_score = scores["total_score"]
        
        if "ai_comment" in scores:
            submission.ai_comment = scores["ai_comment"]
        
        if "ai_score_status" in scores:
            submission.ai_score_status = scores["ai_score_status"]
        
        if "ai_score_detail" in scores:
            submission.ai_score_detail = scores["ai_score_detail"]
        
        db.commit()
        logger.info(f"提交 {submission_id} 评分更新成功，总分: {submission.total_score}")
    except Exception as e:
        logger.error(f"更新提交 {submission_id} 评分失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def update_scores_v2(submission_id: int, scores: dict):
    return update_scores(submission_id, scores)


def update_ai_score_status(
    submission_id: int, 
    status: str, 
    error_message: str = None,
    ai_scored: bool = None,
    ai_scored_at: datetime = None,
    ai_scored_by: str = None
):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"提交 {submission_id} 不存在")
            return
        
        submission.ai_score_status = status
        
        if error_message is not None:
            submission.ai_score_error = error_message
        
        if status == "completed" and ai_scored is None:
            ai_scored = True
        elif status == "failed" and ai_scored is None:
            ai_scored = False
        
        if ai_scored is not None:
            submission.ai_scored = ai_scored
        
        if ai_scored_at is not None:
            submission.ai_scored_at = ai_scored_at
        elif status == "completed" and ai_scored:
            submission.ai_scored_at = datetime.now()
        
        if ai_scored_by is not None:
            submission.ai_scored_by = ai_scored_by
        
        db.commit()
        logger.info(f"提交 {submission_id} AI评分状态更新为: {status}")
    except Exception as e:
        logger.error(f"更新提交 {submission_id} AI评分状态失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_ai_score_status(submission_id: int) -> dict:
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            return {
                "ai_score_status": submission.ai_score_status,
                "ai_score_error": submission.ai_score_error,
                "ai_scored": bool(submission.ai_scored) if submission.ai_scored is not None else False,
                "ai_scored_at": submission.ai_scored_at,
                "ai_scored_by": submission.ai_scored_by
            }
        return None
    except Exception as e:
        logger.error(f"获取提交 {submission_id} AI评分状态失败: {e}")
        return None
    finally:
        db.close()


def review_submission(submission_id: int, review_data: dict = None, 
                      teacher_username: str = None, teacher_by: str = None, 
                      reviewed_by: str = None, scores_dict: dict = None,
                      teacher_comment: str = None, 
                      indicator_scores: dict = None,
                      **kwargs):
    """
    教师审批提交
    ✅ 核心逻辑：只保存指标分数，维度分数由后端重新计算
    """
    print("=" * 60)
    print(f"🔍 review_submission 被调用")
    print(f"   submission_id: {submission_id}")
    print(f"   scores_dict: {scores_dict}")
    print(f"   indicator_scores: {indicator_scores}")
    print(f"   teacher_comment: {teacher_comment}")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"提交 {submission_id} 不存在")
            return
        
        # ========== 1. 更新审批状态 ==========
        submission.is_reviewed = 1
        submission.reviewed_at = datetime.now()
        
        comment = teacher_comment or review_data.get("teacher_comment") if review_data else None
        if comment:
            submission.teacher_comment = comment
        
        reviewer = teacher_username or teacher_by or reviewed_by
        if reviewer:
            submission.reviewed_by = reviewer
        
        # ========== 2. 处理指标分数 ==========
        indicator_scores_data = indicator_scores or (review_data.get("indicator_scores") if review_data else {})
        
        # 如果没有直接的 indicator_scores，尝试从 scores_dict 中提取指标分数
        if not indicator_scores_data and scores_dict:
            # 兼容旧版本：如果 scores_dict 中包含 A1, A2, ... 这样的指标key
            for key in scores_dict:
                if key in ['A1','A2','A3','A4','B1','B2','B3','C1','C2','C3','D1','D2','D3']:
                    indicator_scores_data[key] = scores_dict[key]
        
        # ========== 3. 获取任务的满分信息和启用指标 ==========
        from backend.database.models import TaskRubric, TaskRubricIndicator
        from backend.database.tasks import get_task as get_task_db
        from backend.config import SCORING_DIMENSIONS
        from backend.core.calculators.grade_mapper import score_to_level
        
        task = get_task_db(submission.task_id)
        
        # 获取启用指标
        enabled_indicators = task.get("enabled_indicators", []) if task else []
        if isinstance(enabled_indicators, str):
            enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
        
        # 获取指标满分
        indicator_max_scores = {}
        task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == submission.task_id).first()
        if task_rubric:
            indicators = db.query(TaskRubricIndicator).filter(
                TaskRubricIndicator.task_rubric_id == task_rubric.id
            ).all()
            for ind in indicators:
                indicator_max_scores[ind.indicator_key] = ind.max_score
        
        # ========== 4. 更新指标分数到 submission_scores 表 ==========
        if indicator_scores_data:
            existing_scores = db.query(SubmissionScore).filter(
                SubmissionScore.submission_id == submission_id
            ).all()
            existing_dict = {s.indicator_key: s for s in existing_scores}
            
            for key, value in indicator_scores_data.items():
                if value is None:
                    continue
                
                # 计算等级
                max_score = indicator_max_scores.get(key, 10)
                percent = (value / max_score * 100) if max_score > 0 else 0
                level = score_to_level(percent)
                
                if key in existing_dict:
                    existing_dict[key].score = float(value)
                    existing_dict[key].level = level
                    existing_dict[key].comment = "教师调整"
                else:
                    new_score = SubmissionScore(
                        submission_id=submission_id,
                        indicator_key=key,
                        score=float(value),
                         ai_original_score=float(value),
                        level=level,
                        comment="教师调整"
                    )
                    db.add(new_score)
                logger.info(f"✅ 保存指标 {key} = {value} (满分{max_score})")
        
        # ========== 5. 重新计算维度分数（百分制） ==========
        # 获取所有指标分数（包括刚更新的）
        all_scores = db.query(SubmissionScore).filter(
            SubmissionScore.submission_id == submission_id
        ).all()
        indicator_score_dict = {s.indicator_key: s.score for s in all_scores}
        
        dimension_scores = {}
        for dim in SCORING_DIMENSIONS:
            key = dim["key"]
            indicators = dim.get("sub_indicators", [])
            
            if indicators:
                dim_actual = 0
                dim_max = 0
                has_score = False
                
                for ind in indicators:
                    ind_key = ind["key"]
                    # 只计算启用且已评分的指标
                    if enabled_indicators and ind_key not in enabled_indicators:
                        continue
                    if ind_key in indicator_score_dict:
                        score = indicator_score_dict[ind_key]
                        if score > 0:
                            dim_actual += score
                            dim_max += indicator_max_scores.get(ind_key, 10)
                            has_score = True
                
                if has_score and dim_max > 0:
                    dimension_scores[key] = round((dim_actual / dim_max) * 100, 2)
                else:
                    dimension_scores[key] = 0.0
            else:
                dimension_scores[key] = 0.0
        
        print(f"🔍 重新计算的维度分数: {dimension_scores}")
        
        # ========== 6. 保存维度分数到 submissions 表 ==========
        for key, value in dimension_scores.items():
            setattr(submission, f"final_score_{key}", value)
            logger.info(f"✅ 保存 final_score_{key} = {value}")
        
        # ========== 7. 计算并保存总分 ==========
        # ✅ 总分 = 所有指标得分直接相加
        total_score = 0
        for key, score in indicator_score_dict.items():
            # 只计算启用指标
            if not enabled_indicators or key in enabled_indicators:
                total_score += score
        
        submission.total_score = round(total_score, 2)
        logger.info(f"✅ 保存总分: {submission.total_score}")
        
        # ========== 8. 如果前端传了维度分数但没传指标分数（兼容旧版本） ==========
        if not indicator_scores_data and scores_dict:
            # 检查是否传了维度分数（ai_retrieval, critical, ...）
            dim_keys = ['ai_retrieval', 'critical', 'ethics', 'integration']
            has_dimension_scores = any(k in scores_dict for k in dim_keys)
            
            if has_dimension_scores and not indicator_scores_data:
                # 直接使用前端传来的维度分数
                for key in dim_keys:
                    if key in scores_dict:
                        setattr(submission, f"final_score_{key}", float(scores_dict[key]))
                logger.info(f"⚠️ 兼容模式：使用前端传来的维度分数")
                
                # 计算总分
                valid_scores = [float(scores_dict[k]) for k in dim_keys if k in scores_dict and scores_dict[k] > 0]
                if valid_scores:
                    submission.total_score = round(sum(valid_scores) / len(valid_scores), 2)
        
        db.commit()
        logger.info(f"提交 {submission_id} 审批完成")
        return True
        
    except Exception as e:
        logger.error(f"审批提交 {submission_id} 失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def publish_submission_score(submission_id: int):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"提交 {submission_id} 不存在")
            return
        
        submission.score_published = 1
        db.commit()
        logger.info(f"提交 {submission_id} 成绩已发布")
    except Exception as e:
        logger.error(f"发布成绩失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def save_evaluation_report(submission_id: int, report_data: dict):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"提交 {submission_id} 不存在")
            return
        
        submission.evaluation_report = json.dumps(report_data, ensure_ascii=False)
        submission.report_generated_at = datetime.now()
        db.commit()
        logger.info(f"提交 {submission_id} 测评报告已保存")
    except Exception as e:
        logger.error(f"保存测评报告失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_evaluation_report(submission_id: int) -> Optional[dict]:
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission or not submission.evaluation_report:
            return None
        
        return json.loads(submission.evaluation_report)
    except Exception as e:
        logger.error(f"获取测评报告失败: {e}")
        return None
    finally:
        db.close()