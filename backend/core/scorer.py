"""
AI评分引擎 - 主入口
"""
import logging
import random
from typing import Dict

from .clients.deepseek_client import call_deepseek_api_json
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
    
    # 获取指标级提示词和满分配置
    indicator_prompts = {}
    indicator_max_scores = {}
    rubric_config = task.get("rubric_config", {})
    
    for ind in rubric_config.get("indicators", []):
        ind_key = ind.get("indicator_key")
        if ind_key:
            if ind.get("prompt"):
                indicator_prompts[ind_key] = ind["prompt"]
            indicator_max_scores[ind_key] = ind.get("max_score", 10)
    
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
    
    # 计算各指标实际得分（按满分折算 + 截断确保不超出满分）
    final_indicator_scores = {}
    for key, score in parsed["indicator_scores"].items():
        max_score = indicator_max_scores.get(key, 10)
        raw_score = round(score / 100 * max_score, 2)
        print(f"🔍 指标 {key}: AI评分={score}, max_score={max_score}, raw_score={raw_score}")
        final_indicator_scores[key] = max(0.0, min(raw_score, float(max_score)))
        print(f"🔍 指标 {key}: 最终得分={final_indicator_scores[key]}")
    
    # ✅ 使用 dimension_calculator 的 calculate_dimension_scores 函数
    dimension_scores = calculate_dimension_scores(
        final_indicator_scores,
        enabled_indicators,
        indicator_max_scores
    )
    
    dimension_levels = {dim: score_to_level(score) for dim, score in dimension_scores.items()}
    
    # 计算作业总分 = 所有指标得分直接相加
    total_score = sum(final_indicator_scores.values())
    
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

def score_final_report(task: Dict, content: str) -> Dict:
    """
    对期末报告进行AI评分
    """
    prompt = build_final_report_prompt(task, content)
    response = call_deepseek_api_json(prompt)
    
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
    
    # ✅ 修复：从 backend.config 导入 SCORING_DIMENSIONS
    from backend.config import SCORING_DIMENSIONS
    
    # 计算维度得分（使用实际满分）
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
    
    total_score = sum(indicator_scores.values())
    
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