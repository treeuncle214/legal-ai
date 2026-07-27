"""
评分服务
"""
from typing import Dict, Any, Optional
from backend.core.scorer import score_submission
from backend.database.submissions import update_scores, update_ai_score_status
import logging

logger = logging.getLogger(__name__)


class ScoringService:
    """评分服务类"""
    
    @staticmethod
    async def score_and_save_submission(submission_id: int, task: Dict, submission: Dict) -> Dict:
        """异步评分并保存结果"""
        try:
            # 更新状态为评分中
            update_ai_score_status(submission_id, "scoring")
            
            # 调用AI评分
            result = score_submission(task, submission)
            
            # 保存评分结果到数据库
            dimension_scores = result.get("dimension_scores", {})
            
            scores_dict = {
                "score_ai_retrieval": dimension_scores.get("ai_retrieval", 0),
                "score_critical": dimension_scores.get("critical", 0),
                "score_ethics": dimension_scores.get("ethics", 0),
                "score_integration": dimension_scores.get("integration", 0),
                "ai_comment": result.get("comment", "AI评分完成"),
                "ai_score_status": "completed",
                "ai_score_detail": result.get("indicator_grades", {}) if "indicator_grades" in result else result.get("module_scores", {})
            }
            
            update_scores(submission_id, scores_dict)
            
            logger.info(f"提交 {submission_id} 评分完成")
            return result
            
        except Exception as e:
            logger.error(f"评分失败: {e}", exc_info=True)
            # 保存错误信息
            update_ai_score_status(submission_id, "failed", error_message=str(e))
            raise


async def score_and_save_submission(submission_id: int, task: Dict, submission: Dict) -> Dict:
    """便捷函数：异步评分并保存结果"""
    return await ScoringService.score_and_save_submission(submission_id, task, submission)