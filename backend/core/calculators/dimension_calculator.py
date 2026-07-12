"""
维度得分计算器
"""
from typing import Dict, List, Optional
from .grade_mapper import GRADE_TO_SCORE

# 维度配置
SCORING_DIMENSIONS = {
    "ai_retrieval": {"name": "AI融合智能检索能力", "weight": 0.30, "indicators": ["A1", "A2", "A3", "A4"]},
    "critical": {"name": "批判性评估能力", "weight": 0.20, "indicators": ["B1", "B2", "B3"]},
    "ethics": {"name": "伦理合规辨识能力", "weight": 0.20, "indicators": ["C1", "C2", "C3"]},
    "integration": {"name": "信息整合应用能力", "weight": 0.30, "indicators": ["D1", "D2", "D3"]}
}


def calculate_dimension_scores(
    indicator_scores: Dict[str, float],
    enabled_indicators: List[str] = None
) -> Dict[str, float]:
    """
    根据指标得分计算各维度得分
    只计算启用且实际有得分的指标
    """
    dimension_scores = {}
    dimension_indicator_counts = {}
    
    for dim_key, dim_info in SCORING_DIMENSIONS.items():
        indicators = dim_info["indicators"]
        
        # 如果指定了启用指标，只考虑启用的
        if enabled_indicators:
            indicators = [i for i in indicators if i in enabled_indicators]
        
        # 收集该维度下所有有得分的指标
        scores = []
        for ind in indicators:
            if ind in indicator_scores and indicator_scores[ind] is not None:
                scores.append(indicator_scores[ind])
        
        if scores:
            dimension_scores[dim_key] = round(sum(scores) / len(scores), 2)
        else:
            # 该维度所有指标都未被评分，给0分（表示完全未体现该能力）
            dimension_scores[dim_key] = 0.0
    
    return dimension_scores


def calculate_dimension_levels(dimension_scores: Dict[str, float]) -> Dict[str, str]:
    """计算维度等级"""
    from .grade_mapper import score_to_level
    return {dim: score_to_level(score) for dim, score in dimension_scores.items()}


def calculate_total_score(
    dimension_scores: Dict[str, float],
    weights: Dict[str, float] = None
) -> float:
    """计算加权总分"""
    if weights is None:
        weights = {dim: info["weight"] for dim, info in SCORING_DIMENSIONS.items()}
    
    total = 0.0
    total_weight = 0.0
    
    for dim_key, score in dimension_scores.items():
        weight = weights.get(dim_key, 0.25)
        total += score * weight
        total_weight += weight
    
    # 如果总分不为0，归一化
    if total_weight > 0:
        total = total / total_weight * 100 if total_weight != 1 else total
    
    return round(total, 2)