"""
提交评分相关操作
"""
import json
import logging
from datetime import datetime
from typing import Optional

from backend.database.engine import get_db_connection, SessionLocal
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
        
        if "ai_comment" in scores:
            submission.ai_comment = scores["ai_comment"]
        
        if "ai_score_status" in scores:
            submission.ai_score_status = scores["ai_score_status"]
        
        if "ai_score_detail" in scores:
            submission.ai_score_detail = scores["ai_score_detail"]
        
        db.commit()
        logger.info(f"提交 {submission_id} 评分更新成功")
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
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ai_score_status, ai_score_error, ai_scored, ai_scored_at, ai_scored_by
            FROM submissions 
            WHERE id = ?
        """, (submission_id,))
        row = cursor.fetchone()
        if row:
            return {
                "ai_score_status": row[0],
                "ai_score_error": row[1],
                "ai_scored": bool(row[2]) if row[2] is not None else False,
                "ai_scored_at": row[3],
                "ai_scored_by": row[4]
            }
        return None
    except Exception as e:
        logger.error(f"获取提交 {submission_id} AI评分状态失败: {e}")
        return None
    finally:
        conn.close()


def review_submission(submission_id: int, review_data: dict = None, 
                      teacher_username: str = None, teacher_by: str = None, 
                      reviewed_by: str = None, scores_dict: dict = None,
                      teacher_comment: str = None, 
                      indicator_scores: dict = None,
                      **kwargs):
    """
    教师审批提交
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
        
        submission.is_reviewed = 1
        submission.reviewed_at = datetime.now()
        
        if review_data is None:
            review_data = {}
        
        comment = teacher_comment or review_data.get("teacher_comment")
        if comment:
            submission.teacher_comment = comment
        
        reviewer = teacher_username or teacher_by or reviewed_by or review_data.get("reviewed_by")
        if reviewer:
            submission.reviewed_by = reviewer
        
        # ========== 保存维度分数 ==========
        scores = scores_dict or review_data.get("scores", {})
        if scores:
            for key, value in scores.items():
                if key in ['ai_retrieval', 'critical', 'ethics', 'integration']:
                    setattr(submission, f"final_score_{key}", float(value))
                    logger.info(f"✅ 保存 final_score_{key} = {value}")
                elif key.startswith("final_score_"):
                    setattr(submission, key, float(value))
                    logger.info(f"✅ 保存 {key} = {value}")
            
            # ========== ✅ 计算并保存总分 ==========
            # ✅ 正确逻辑：所有指标得分直接相加
            indicator_scores_data = indicator_scores or review_data.get("indicator_scores", {})
            
            if indicator_scores_data:
                # 所有指标得分直接相加
                total = sum(indicator_scores_data.values())
                submission.total_score = round(total, 2)
                logger.info(f"✅ 保存总分: {submission.total_score} (由指标得分相加: {indicator_scores_data})")
            else:
                # 降级方案：从已保存的指标分数计算（如果 indicator_scores 为空）
                existing_scores = db.query(SubmissionScore).filter(
                    SubmissionScore.submission_id == submission_id
                ).all()
                if existing_scores:
                    total = sum([s.score for s in existing_scores])
                    submission.total_score = round(total, 2)
                    logger.info(f"✅ 保存总分: {submission.total_score} (从数据库指标计算)")
                else:
                    # 如果连指标都没有，使用维度得分的平均（兼容旧数据）
                    valid_scores = []
                    for key in ['ai_retrieval', 'critical', 'ethics', 'integration']:
                        value = scores.get(key, 0)
                        if value > 0:
                            valid_scores.append(value)
                    if valid_scores:
                        total = sum(valid_scores) / len(valid_scores)
                        submission.total_score = round(total, 2)
                        logger.info(f"✅ 保存总分: {submission.total_score} (维度平均-降级)")
                    else:
                        submission.total_score = 0
                        logger.info(f"✅ 无有效得分，总分设为 0")
        
        # ========== 更新指标分数 ==========
        indicator_scores_data = indicator_scores or review_data.get("indicator_scores", {})
        
        if indicator_scores_data:
            existing_scores = db.query(SubmissionScore).filter(
                SubmissionScore.submission_id == submission_id
            ).all()
            
            existing_dict = {s.indicator_key: s for s in existing_scores}
            
            for key, value in indicator_scores_data.items():
                if value >= 8.5:
                    level = "优"
                elif value >= 7.0:
                    level = "良"
                elif value >= 5.5:
                    level = "合格"
                else:
                    level = "不合格"
                
                if key in existing_dict:
                    existing_dict[key].score = float(value)
                    existing_dict[key].level = level
                    existing_dict[key].comment = "教师调整"
                    logger.info(f"✅ 更新指标 {key} = {value}")
                else:
                    new_score = SubmissionScore(
                        submission_id=submission_id,
                        indicator_key=key,
                        score=float(value),
                        level=level,
                        comment="教师调整"
                    )
                    db.add(new_score)
                    logger.info(f"✅ 新增指标 {key} = {value}")
        
        db.commit()
        logger.info(f"提交 {submission_id} 审批完成，审批人: {reviewer}")
    except Exception as e:
        logger.error(f"审批提交 {submission_id} 失败: {e}")
        db.rollback()
        raise
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