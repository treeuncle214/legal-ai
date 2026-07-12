# backend/core/parsers/module_parser.py
"""
期末报告模块评分解析器
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 7个模块配置（与提示词保持一致）
MODULE_CONFIG = {
    "问题界定与关键词提取": {"weight": 0.15, "indicators": ["A1", "A2"]},
    "AI工具使用与策略优化": {"weight": 0.15, "indicators": ["A3", "A4"]},
    "信息源评估与筛选": {"weight": 0.10, "indicators": ["B1", "B2", "B3"]},
    "伦理合规与学术诚信": {"weight": 0.10, "indicators": ["C1", "C2", "C3"]},
    "信息整合与结构化": {"weight": 0.10, "indicators": ["D1"]},
    "法律分析与推理": {"weight": 0.15, "indicators": ["D2"]},
    "结论与建议": {"weight": 0.15, "indicators": ["D3"]},
}

# 模块到维度的映射
MODULE_TO_DIMENSION = {
    "问题界定与关键词提取": "ai_retrieval",
    "AI工具使用与策略优化": "ai_retrieval",
    "信息源评估与筛选": "critical",
    "伦理合规与学术诚信": "ethics",
    "信息整合与结构化": "integration",
    "法律分析与推理": "integration",
    "结论与建议": "integration",
}


def parse_module_scores(ai_response: Dict) -> Dict:
    """
    解析AI返回的模块评分
    
    输入格式:
    {
        "module_scores": {
            "问题界定与关键词提取": 85,
            "AI工具使用与策略优化": 80,
            ...
        },
        "module_comments": {
            "问题界定与关键词提取": "评语...",
            ...
        },
        "comment": "整体评价..."
    }
    
    输出格式:
    {
        "module_scores": {"问题界定与关键词提取": 85, ...},
        "module_comments": {"问题界定与关键词提取": "评语...", ...},
        "overall_comment": "整体评价...",
        "dimension_mapping": {
            "ai_retrieval": {"modules": ["问题界定...", "AI工具..."], "score": 82.5},
            ...
        }
    }
    """
    result = {
        "module_scores": {},
        "module_comments": {},
        "overall_comment": "",
        "dimension_mapping": {},
        "indicator_scores": {},  # 方便统一处理
        "indicator_levels": {},
        "indicator_comments": {},
    }
    
    # 1. 提取模块分数
    module_scores = ai_response.get("module_scores", {})
    module_comments = ai_response.get("module_comments", {})
    
    if not module_scores:
        logger.warning("AI返回的模块分数为空，使用默认值")
        module_scores = generate_default_module_scores()
    
    result["module_scores"] = module_scores
    result["overall_comment"] = ai_response.get("comment", "评分完成")
    
    # 2. 提取模块评语（如果有）
    for module_name in module_scores.keys():
        comment = module_comments.get(module_name, "")
        result["module_comments"][module_name] = comment if comment else f"{module_scores[module_name]}分"
    
    # 3. 计算维度映射
    dimension_scores = {}
    dimension_comments = {}
    
    for module_name, score in module_scores.items():
        dimension = MODULE_TO_DIMENSION.get(module_name)
        if dimension:
            if dimension not in dimension_scores:
                dimension_scores[dimension] = []
                dimension_comments[dimension] = []
            dimension_scores[dimension].append(score)
            if module_name in result["module_comments"]:
                dimension_comments[dimension].append(result["module_comments"][module_name])
    
    # 4. 生成维度映射结果
    for dimension, scores in dimension_scores.items():
        avg_score = round(sum(scores) / len(scores), 2) if scores else 60.0
        result["dimension_mapping"][dimension] = {
            "modules": [m for m in MODULE_TO_DIMENSION.keys() if MODULE_TO_DIMENSION[m] == dimension],
            "scores": scores,
            "avg_score": avg_score,
            "comments": dimension_comments.get(dimension, [])
        }
    
    # 5. 转换为指标级评分（便于统一展示）
    # 将模块分数映射到指标（一个模块可能对应多个指标）
    for module_name, score in module_scores.items():
        indicators = MODULE_CONFIG.get(module_name, {}).get("indicators", [])
        comment = result["module_comments"].get(module_name, f"{score}分")
        for indicator in indicators:
            result["indicator_scores"][indicator] = score
            result["indicator_levels"][indicator] = score_to_level(score)
            result["indicator_comments"][indicator] = f"[{module_name}] {comment}"
    
    return result


def score_to_level(score: float) -> str:
    """分数转等级"""
    if score >= 85:
        return "优"
    elif score >= 75:
        return "良"
    elif score >= 55:
        return "合格"
    else:
        return "不合格"


def generate_default_module_scores() -> Dict[str, int]:
    """生成默认模块分数（AI返回为空时使用）"""
    return {
        "问题界定与关键词提取": 70,
        "AI工具使用与策略优化": 70,
        "信息源评估与筛选": 70,
        "伦理合规与学术诚信": 70,
        "信息整合与结构化": 70,
        "法律分析与推理": 70,
        "结论与建议": 70,
    }


def extract_module_score(ai_response: Dict, module_name: str, default: int = 60) -> int:
    """安全提取单个模块分数"""
    module_scores = ai_response.get("module_scores", {})
    return module_scores.get(module_name, default)


def extract_all_module_scores(ai_response: Dict) -> Dict[str, int]:
    """提取所有模块分数"""
    return ai_response.get("module_scores", generate_default_module_scores())


def get_modules_by_dimension(dimension: str) -> List[str]:
    """获取某个维度对应的模块列表"""
    return [m for m, d in MODULE_TO_DIMENSION.items() if d == dimension]


def get_indicators_by_module(module_name: str) -> List[str]:
    """获取某个模块对应的指标列表"""
    return MODULE_CONFIG.get(module_name, {}).get("indicators", [])