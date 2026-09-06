"""
AI评分引擎 - 主入口
"""
import logging
import random
from typing import Dict

from .clients.deepseek_client import call_deepseek_api_json
from .prompts.exercise_prompt import build_exercise_prompt
from .parsers.indicator_parser import parse_indicator_scores, get_all_indicators
from .calculators.dimension_calculator import calculate_dimension_scores
from .calculators.grade_mapper import score_to_level

logger = logging.getLogger(__name__)


def _build_default_rubric_config(enabled_indicators):
    """构建默认评分配置（所有指标满分10分）"""
    from backend.config import SCORING_DIMENSIONS
    indicators = []
    for dim in SCORING_DIMENSIONS:
        for ind in dim.get("sub_indicators", []):
            if enabled_indicators and ind["key"] not in enabled_indicators:
                continue
            indicators.append({
                "indicator_key": ind["key"],
                "max_score": 10,
                "prompt": ""
            })
    return {
        "overall_prompt": None,
        "indicators": indicators
    }


def score_exercise(task: Dict, submission: Dict) -> Dict:
    """
    对平时练习进行AI评分
    """
    # 获取启用指标
    enabled_indicators = task.get("enabled_indicators", [])
    if isinstance(enabled_indicators, str):
        enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
    
    # ✅ 安全获取 rubric_config（如果为 None 或空，使用默认配置）
    rubric_config = task.get("rubric_config") or {}
    
    # ✅ 如果 rubric_config 没有指标，使用默认配置
    if not rubric_config.get("indicators"):
        rubric_config = _build_default_rubric_config(enabled_indicators)
        logger.warning("⚠️ rubric_config 为空，使用默认配置（所有指标满分10分）")
    
    # 获取指标级提示词和满分配置
    indicator_prompts = {}
    indicator_max_scores = {}
    
    for ind in rubric_config.get("indicators", []) or []:
        if not ind:
            continue
        ind_key = ind.get("indicator_key")
        if ind_key:
            if ind.get("prompt"):
                indicator_prompts[ind_key] = ind["prompt"]
            indicator_max_scores[ind_key] = ind.get("max_score", 10)
    
    # ✅ 确保所有启用指标都有满分配置
    if enabled_indicators:
        for key in enabled_indicators:
            if key not in indicator_max_scores:
                indicator_max_scores[key] = 10
    
    # 构建Prompt（传入 indicator_max_scores 供AI参考）
    prompt = build_exercise_prompt(
        task,
        submission,
        enabled_indicators,
        indicator_prompts,
        indicator_max_scores
    )
    
    # 调用AI
    response = call_deepseek_api_json(prompt)
    
    # 如果AI调用失败，使用模拟评分
    if response is None:
        return generate_fallback_score(task, submission, indicator_max_scores)
    
    # 解析指标评分（AI返回0-100分）
    parsed = parse_indicator_scores(response)
    
    # 计算各指标实际得分：AI 返回 0-100，按各指标满分折算（score/100 × max_score）
    final_indicator_scores = {}
    for key, score in parsed["indicator_scores"].items():
        max_score = indicator_max_scores.get(key, 10)
        final_indicator_scores[key] = round(score / 100 * max_score, 2)
    
    # 使用 dimension_calculator 的 calculate_dimension_scores 函数
    dimension_scores = calculate_dimension_scores(
        final_indicator_scores,
        enabled_indicators,
        indicator_max_scores
    )
    
    dimension_levels = {dim: score_to_level(score) for dim, score in dimension_scores.items()}
    
    # 计算作业总分 = 所有指标得分之和 / 满分之和 × 100（百分制，与维度得分同口径）
    total_raw = sum(final_indicator_scores.values())
    total_max = sum(indicator_max_scores.get(k, 10) for k in final_indicator_scores)
    total_score = round(total_raw / total_max * 100, 2) if total_max > 0 else 0.0
    
    # 指标等级
    indicator_grades = {}
    for key, score in final_indicator_scores.items():
        max_score = indicator_max_scores.get(key, 10)
        percent = (score / max_score * 100) if max_score > 0 else 0
        indicator_grades[key] = score_to_level(percent)
    
    return {
        "indicator_grades": indicator_grades,
        "indicator_scores": final_indicator_scores,
        "indicator_levels": parsed["indicator_levels"],
        "indicator_comments": parsed["indicator_comments"],
        "dimension_scores": dimension_scores,
        "dimension_levels": dimension_levels,
        "ai_comment": parsed["overall_comment"],
        "total_score": round(total_score, 2),
        "raw_scores": parsed["indicator_scores"],
        "indicator_max_scores": indicator_max_scores,
        "metadata": {
            "enabled_indicators": enabled_indicators,
            "prompt_type": "exercise"
        }
    }


def generate_fallback_score(task: Dict, submission: Dict, indicator_max_scores: Dict = None) -> Dict:
    """生成降级评分（AI不可用时）"""
    enabled_indicators = task.get("enabled_indicators", [])
    if isinstance(enabled_indicators, str):
        enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
    
    all_indicators = get_all_indicators()
    
    if indicator_max_scores is None:
        indicator_max_scores = {key: 10 for key in all_indicators}
    
    import random
    indicator_scores = {}
    indicator_comments = {}
    
    for key in all_indicators:
        if not enabled_indicators or key in enabled_indicators:
            max_score = indicator_max_scores.get(key, 10)
            score = round(random.uniform(max_score * 0.4, max_score * 0.9), 1)
            indicator_scores[key] = max(0.0, min(score, float(max_score)))
            indicator_comments[key] = f"AI服务暂时不可用，此为临时评分（{indicator_scores[key]}/{max_score}分），请教师重新审批。"
    
    from backend.config import SCORING_DIMENSIONS
    
    dimension_scores = {}
    for dim in SCORING_DIMENSIONS:
        key = dim["key"]
        sub_indicators = dim.get("sub_indicators", [])
        if sub_indicators:
            dim_total = 0.0
            dim_max = 0.0
            has_score = False
            for ind in sub_indicators:
                ind_key = ind["key"]
                if not enabled_indicators or ind_key in enabled_indicators:
                    score = indicator_scores.get(ind_key, 0.0)
                    max_score = indicator_max_scores.get(ind_key, 10.0)
                    dim_total += score
                    dim_max += max_score
                    if score > 0:
                        has_score = True
            if has_score and dim_max > 0:
                dimension_scores[key] = round((dim_total / dim_max) * 100, 2)
            else:
                dimension_scores[key] = 0.0
        else:
            dimension_scores[key] = 0.0
    
    total_raw = sum(indicator_scores.values())
    total_max = sum(indicator_max_scores.get(k, 10) for k in indicator_scores)
    total_score = round(total_raw / total_max * 100, 2) if total_max > 0 else 0.0
    
    return {
        "indicator_grades": {k: score_to_level((v / indicator_max_scores.get(k, 10)) * 100) for k, v in indicator_scores.items()},
        "indicator_scores": indicator_scores,
        "indicator_levels": {k: score_to_level((v / indicator_max_scores.get(k, 10)) * 100) for k, v in indicator_scores.items()},
        "indicator_comments": indicator_comments,
        "dimension_scores": dimension_scores,
        "dimension_levels": {dim: score_to_level(score) for dim, score in dimension_scores.items()},
        "ai_comment": "⚠️ AI评分服务暂时不可用，当前为模拟评分，请教师重新审批。",
        "total_score": round(total_score, 2),
        "indicator_max_scores": indicator_max_scores,
        "metadata": {"prompt_type": "fallback", "enabled_indicators": enabled_indicators}
    }


def score_submission(task: Dict, submission: Dict) -> Dict:
    """统一的评分入口：课堂练习 / 任务实践 / 期末考察 均使用 13 指标评分"""
    return score_exercise(task, submission)


def test_api():
    """测试API连通性"""
    from .clients.deepseek_client import test_api as _test_api
    return _test_api()