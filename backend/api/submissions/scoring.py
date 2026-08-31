"""
AI评分核心逻辑
"""
import json
import logging
from datetime import datetime

from backend.database import update_scores, get_task
from backend.database.submissions import get_submission, update_ai_score_status
from backend.core.scorer import score_submission
from backend.core.report_generator import generate_report
from backend.database.models import Submission, SubmissionScore, TaskRubric, TaskRubricIndicator
from backend.database.engine import SessionLocal

logger = logging.getLogger(__name__)


async def perform_scoring(submission_id: int, task_dict: dict, content: str, submit_type: str, teacher_username: str = None):
    """
    执行AI评分
    - teacher_username: 触发评分的教师（用于记录）
    """
    try:
        logger.info(f"开始为提交 {submission_id} 进行AI评分，触发人: {teacher_username or '系统'}")
        update_ai_score_status(submission_id, "scoring")
        
        # ✅ 关键修复：总是从数据库重新获取完整的任务信息
        task_id = task_dict.get("id") if task_dict else None
        if task_id:
            fresh_task = get_task(task_id)
            if fresh_task:
                task_dict = fresh_task
                logger.info(f"✅ 已获取任务 {task_id} 完整信息")
                if task_dict.get("rubric_config"):
                    logger.info(f"   rubric_config 指标数: {len(task_dict['rubric_config'].get('indicators', []))}")
                else:
                    logger.warning("⚠️ rubric_config 为 None，scorer.py 将使用默认配置")
        
        # 从数据库获取完整的提交信息
        submission = get_submission(submission_id)
        if not submission:
            logger.error(f"提交 {submission_id} 不存在")
            update_ai_score_status(submission_id, "failed", error_message="提交记录不存在")
            return
        
        # 构建完整的评分数据
        score_data = {
            "process_log": submission.get("process_log", ""),
            "ai_interaction_log": submission.get("ai_interaction_log", ""),
            "final_output": submission.get("final_output", ""),
            "submit_type": submit_type,
            "word_file_path": submission.get("word_file_path", ""),
        }
        
        # 调用评分引擎
        score_result = score_submission(task_dict, score_data)
        
        # ✅ 确保 score_result 包含 indicator_max_scores
        if "indicator_max_scores" not in score_result or not score_result["indicator_max_scores"]:
            db_temp = SessionLocal()
            try:
                task_rubric = db_temp.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
                if task_rubric:
                    indicators = db_temp.query(TaskRubricIndicator).filter(
                        TaskRubricIndicator.task_rubric_id == task_rubric.id
                    ).all()
                    indicator_max_scores = {ind.indicator_key: ind.max_score for ind in indicators}
                    score_result["indicator_max_scores"] = indicator_max_scores
                    logger.info(f"从数据库查询到满分信息: {indicator_max_scores}")
            finally:
                db_temp.close()
        
        # 准备评分数据
        scores_dict = {
            "score_ai_retrieval": score_result["dimension_scores"].get("ai_retrieval", 0),
            "score_critical": score_result["dimension_scores"].get("critical", 0),
            "score_ethics": score_result["dimension_scores"].get("ethics", 0),
            "score_integration": score_result["dimension_scores"].get("integration", 0),
            "ai_comment": score_result.get("ai_comment", "AI评分完成"),
            "ai_score_status": "completed",
            "ai_score_detail": json.dumps(score_result.get("indicator_grades", {})) if "indicator_grades" in score_result else json.dumps(score_result.get("module_scores", {})),
            "total_score": score_result.get("total_score", 0)
        }
        update_scores(submission_id, scores_dict)
        
        # 存储每个指标的评分详情
        db = None
        try:
            db = SessionLocal()
            
            indicator_scores = score_result.get("indicator_scores", {})
            indicator_levels = score_result.get("indicator_levels", {})
            indicator_comments = score_result.get("indicator_comments", {})
            indicator_max_scores = score_result.get("indicator_max_scores", {})
            
            if not indicator_max_scores:
                task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
                if task_rubric:
                    indicators = db.query(TaskRubricIndicator).filter(
                        TaskRubricIndicator.task_rubric_id == task_rubric.id
                    ).all()
                    for ind in indicators:
                        indicator_max_scores[ind.indicator_key] = ind.max_score
                    logger.info(f"从数据库查询到满分信息: {indicator_max_scores}")

            valid_keys = ['A1','A2','A3','A4','B1','B2','B3','C1','C2','C3','D1','D2','D3']
            for key, score in indicator_scores.items():
                if key in valid_keys:
                    max_score = indicator_max_scores.get(key, 10)
                    final_score = max(0.0, min(score, float(max_score)))

                    indicator_score = SubmissionScore(
                        submission_id=submission_id,
                        indicator_key=key,
                        score=final_score,
                        ai_original_score=final_score,  # ✅ 保存 AI 原始分数
                        level=indicator_levels.get(key, "合格"),
                        comment=indicator_comments.get(key, "")
                    )
                    db.add(indicator_score)
            db.commit()
            logger.info(f"提交 {submission_id} 指标评分详情已保存")
        except Exception as e:
            logger.error(f"保存指标评分详情失败: {e}")
        finally:
            if db:
                db.close()
        
        # 生成测评报告（包含模板信息和学生内容）
        try:
            # 获取学生提交内容
            student_content = submission.get("word_content", "") or submission.get("final_output", "")
            
            # 获取启用指标
            enabled_indicators = task_dict.get("enabled_indicators", [])
            if isinstance(enabled_indicators, str):
                enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
            
            # 获取模板信息
            teacher_prompt = None
            indicator_details = None
            
            db = SessionLocal()
            try:
                task_rubric = db.query(TaskRubric).filter(TaskRubric.task_id == task_id).first()
                if task_rubric:
                    teacher_prompt = task_rubric.overall_prompt
                    
                    indicators = db.query(TaskRubricIndicator).filter(
                        TaskRubricIndicator.task_rubric_id == task_rubric.id
                    ).all()
                    
                    if indicators:
                        indicator_details = "评分指标详情：\n"
                        indicator_names = {
                            "A1": "问题拆解与检索目标设定",
                            "A2": "检索策略设计",
                            "A3": "AI工具融合应用",
                            "A4": "检索策略优化",
                            "B1": "信息来源评估",
                            "B2": "AI内容验证",
                            "B3": "争议与分歧分析",
                            "C1": "风险类型识别",
                            "C2": "价值综合判断",
                            "C3": "风险处理方式",
                            "D1": "信息分类与组织",
                            "D2": "综合分析与决策",
                            "D3": "局限认知与持续学习"
                        }
                        for ind in indicators:
                            name = indicator_names.get(ind.indicator_key, ind.indicator_key)
                            prompt_text = ind.prompt or "（未设置详细描述）"
                            indicator_details += f"- {ind.indicator_key} {name}: {prompt_text}\n"
            finally:
                db.close()
            
            report_data = generate_report(
                task_title=task_dict.get("title", "法律检索任务"),
                task_type=task_dict.get("task_type", "任务实践"),
                dimension_scores=score_result.get("dimension_scores", {}),
                indicator_scores=score_result.get("indicator_scores", {}),
                ai_comment=score_result.get("ai_comment", ""),
                student_content=student_content,
                teacher_prompt=teacher_prompt,
                indicator_details=indicator_details,
                enabled_indicators=enabled_indicators
            )
            
            if report_data:
                # 保存报告到数据库
                db = SessionLocal()
                try:
                    submission_obj = db.query(Submission).filter(Submission.id == submission_id).first()
                    if submission_obj:
                        submission_obj.evaluation_report = json.dumps(report_data, ensure_ascii=False)
                        submission_obj.report_generated_at = datetime.now()
                        db.commit()
                        logger.info(f"提交 {submission_id} 测评报告已生成")
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"生成测评报告失败: {e}")
        
        # 更新AI评分状态（标记已评分）
        update_ai_score_status(
            submission_id, 
            "completed",
            ai_scored=True,
            ai_scored_at=datetime.now(),
            ai_scored_by=teacher_username
        )
        
        logger.info(f"提交 {submission_id} AI评分完成")
    except Exception as e:
        logger.error(f"提交 {submission_id} AI评分失败: {str(e)}", exc_info=True)
        update_ai_score_status(submission_id, "failed", error_message=str(e))
        update_scores(submission_id, {"ai_comment": "AI评分失败，请教师手动批改", "ai_score_status": "failed"})