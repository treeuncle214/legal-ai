# backend/core/scorer.py
"""
AI评分引擎 - 主入口
"""
import logging
from typing import Dict

from .clients.deepseek_client import call_deepseek_api
from .prompts.exercise_prompt import build_exercise_prompt
from .prompts.final_report_prompt import build_final_report_prompt
from .parsers.indicator_parser import parse_indicator_scores, get_all_indicators
from .parsers.module_parser import parse_module_scores
from .calculators.dimension_calculator import calculate_dimension_scores, calculate_total_score
from .calculators.grade_mapper import score_to_level

logger = logging.getLogger(__name__)


def score_exercise(task: Dict, submission: Dict) -> Dict:
    """
    对平时练习进行AI评分
    """
    # 获取启用指标
    enabled_indicators = task.get("enabled_indicators", [])
    if isinstance(enabled_indicators, str):
        enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
    
    # 获取指标级提示词
    indicator_prompts = {}
    rubric_config = task.get("rubric_config", {})
    for ind in rubric_config.get("indicators", []):
        if ind.get("prompt"):
            indicator_prompts[ind["indicator_key"]] = ind["prompt"]
    
    # 构建Prompt
    prompt = build_exercise_prompt(task, submission, enabled_indicators, indicator_prompts)
    
    # 调用AI
    response = call_deepseek_api(prompt)
    
    # 如果AI调用失败，使用模拟评分
    if response is None:
        return generate_fallback_score(task, submission)
    
    # 解析指标评分
    parsed = parse_indicator_scores(response)
    
    # 计算维度得分
    dimension_scores = calculate_dimension_scores(
        parsed["indicator_scores"],
        enabled_indicators
    )
    dimension_levels = {dim: score_to_level(score) for dim, score in dimension_scores.items()}
    
    # 计算总分
    total_score = calculate_total_score(dimension_scores)
    
    # 获取指标满分配置
    indicator_max_scores = {}
    for ind in rubric_config.get("indicators", []):
        indicator_max_scores[ind["indicator_key"]] = ind["max_score"]
    
    # 计算各指标实际得分（按满分折算）
    final_indicator_scores = {}
    for key, score in parsed["indicator_scores"].items():
        max_score = indicator_max_scores.get(key, 10)
        final_indicator_scores[key] = round(score / 100 * max_score, 2)
    
    return {
        "indicator_grades": {k: score_to_level(v) for k, v in parsed["indicator_scores"].items()},
        "indicator_scores": final_indicator_scores,
        "indicator_levels": parsed["indicator_levels"],
        "indicator_comments": parsed["indicator_comments"],
        "dimension_scores": dimension_scores,
        "dimension_levels": dimension_levels,
        "ai_comment": parsed["overall_comment"],
        "total_score": total_score,
        "raw_scores": parsed["indicator_scores"],  # 保留原始0-100分
        "metadata": {
            "enabled_indicators": enabled_indicators,
            "prompt_type": "exercise"
        }
    }


def score_final_report(task: Dict, content: str) -> Dict:
    """
    对期末报告进行AI评分
    """
    prompt = build_final_report_prompt(task, content)
    response = call_deepseek_api(prompt)
    
    if response is None:
        return generate_fallback_report_score(task, content)
    
    # 解析模块评分
    module_scores = response.get("module_scores", {})
    module_comments = response.get("module_comments", {})
    
    # 映射到维度
    mapping = {
        "ai_retrieval": ["问题界定与关键词提取", "AI工具使用与策略优化"],
        "critical": ["信息源评估与筛选"],
        "ethics": ["伦理合规与学术诚信"],
        "integration": ["信息整合与结构化", "法律分析与推理", "结论与建议"]
    }
    
    dimension_scores = {}
    for dim_key, modules in mapping.items():
        scores = [module_scores.get(module, 0) for module in modules]
        if scores:
            dimension_scores[dim_key] = round(sum(scores) / len(scores), 2)
        else:
            dimension_scores[dim_key] = 60.0
    
    dimension_levels = {dim: score_to_level(score) for dim, score in dimension_scores.items()}
    total_score = calculate_total_score(dimension_scores)
    
    return {
        "module_scores": module_scores,
        "module_comments": module_comments,
        "dimension_scores": dimension_scores,
        "dimension_levels": dimension_levels,
        "ai_comment": response.get("comment", "评分完成"),
        "total_score": total_score,
        "metadata": {"prompt_type": "final_report"}
    }


def generate_fallback_score(task: Dict, submission: Dict) -> Dict:
    """生成降级评分（AI不可用时）"""
    enabled_indicators = task.get("enabled_indicators", [])
    if isinstance(enabled_indicators, str):
        enabled_indicators = [i.strip() for i in enabled_indicators.split(',') if i.strip()]
    
    # 生成差异化的随机分数（60-85分）
    import random
    indicator_scores = {}
    indicator_comments = {}
    all_indicators = get_all_indicators()
    
    for key in all_indicators:
        if not enabled_indicators or key in enabled_indicators:
            # 正态分布，集中在70分左右
            score = int(random.gauss(70, 12))
            score = max(45, min(95, score))
            indicator_scores[key] = score
            indicator_comments[key] = f"AI服务暂时不可用，此为临时评分（{score}分），请教师重新审批。"
    
    dimension_scores = calculate_dimension_scores(indicator_scores, enabled_indicators)
    total_score = calculate_total_score(dimension_scores)
    
    return {
        "indicator_grades": {k: score_to_level(v) for k, v in indicator_scores.items()},
        "indicator_scores": indicator_scores,
        "indicator_levels": {k: score_to_level(v) for k, v in indicator_scores.items()},
        "indicator_comments": indicator_comments,
        "dimension_scores": dimension_scores,
        "dimension_levels": {dim: score_to_level(score) for dim, score in dimension_scores.items()},
        "ai_comment": "⚠️ AI评分服务暂时不可用，当前为模拟评分，请教师重新审批。",
        "total_score": total_score,
        "metadata": {"prompt_type": "fallback", "enabled_indicators": enabled_indicators}
    }


def generate_fallback_report_score(task: Dict, content: str) -> Dict:
    """生成期末报告降级评分"""
    import random
    modules = ["问题界定与关键词提取", "AI工具使用与策略优化", "信息源评估与筛选", 
               "伦理合规与学术诚信", "信息整合与结构化", "法律分析与推理", "结论与建议"]
    
    module_scores = {module: random.randint(60, 90) for module in modules}
    
    mapping = {
        "ai_retrieval": ["问题界定与关键词提取", "AI工具使用与策略优化"],
        "critical": ["信息源评估与筛选"],
        "ethics": ["伦理合规与学术诚信"],
        "integration": ["信息整合与结构化", "法律分析与推理", "结论与建议"]
    }
    
    dimension_scores = {}
    for dim_key, modules in mapping.items():
        scores = [module_scores.get(module, 0) for module in modules]
        if scores:
            dimension_scores[dim_key] = round(sum(scores) / len(scores), 2)
        else:
            dimension_scores[dim_key] = 60.0
    
    total_score = calculate_total_score(dimension_scores)
    
    return {
        "module_scores": module_scores,
        "module_comments": {k: f"{v}分 (临时评分)" for k, v in module_scores.items()},
        "dimension_scores": dimension_scores,
        "dimension_levels": {dim: score_to_level(score) for dim, score in dimension_scores.items()},
        "ai_comment": "⚠️ AI评分服务暂时不可用，当前为模拟评分，请教师重新审批。",
        "total_score": total_score,
        "metadata": {"prompt_type": "fallback_report"}
    }


# 主入口函数（保持向后兼容）
def score_submission(task: Dict, submission: Dict) -> Dict:
    """统一的评分入口"""
    task_type = task.get("task_type", "课堂练习")
    
    if task_type == "期末考察":
        content = submission.get("final_output", "")
        if submission.get("submit_type") == "word":
            content = submission.get("content", content)
        return score_final_report(task, content)
    else:
        return score_exercise(task, submission)


def test_api():
    """测试API连通性"""
    from .clients.deepseek_client import test_api as _test_api
    return _test_api()