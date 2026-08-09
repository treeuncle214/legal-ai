"""
维度得分计算器
"""
from typing import Dict, List, Optional

# 维度配置 - 仅用于定义指标归属和权重
SCORING_DIMENSIONS = {
    "ai_retrieval": {"name": "AI融合智能检索能力", "weight": 0.30, "indicators": ["A1", "A2", "A3", "A4"]},
    "critical": {"name": "批判性评估能力", "weight": 0.20, "indicators": ["B1", "B2", "B3"]},
    "ethics": {"name": "伦理合规辨识能力", "weight": 0.20, "indicators": ["C1", "C2", "C3"]},
    "integration": {"name": "信息整合应用能力", "weight": 0.30, "indicators": ["D1", "D2", "D3"]}
}


def calculate_dimension_scores(
    indicator_scores: Dict[str, float],
    enabled_indicators: List[str] = None,
    indicator_max_scores: Dict[str, float] = None
) -> Dict[str, float]:
    """
    根据指标得分计算各维度得分（百分制）
    
    计算方式：
    维度得分 = (该维度下所有启用指标的得分之和) / (该维度下所有启用指标的满分之和) × 100
    
    参数：
        indicator_scores: 指标得分字典 {'A1': 8.5, 'A2': 7.8, ...}
        enabled_indicators: 启用的指标列表 ['A4', 'B3', 'C3', 'D3']
        indicator_max_scores: 指标满分字典 {'A4': 30, 'B3': 20, 'C3': 15, 'D3': 35}
    
    返回：
        维度得分字典 {'ai_retrieval': 82.0, 'critical': 88.0, ...}
    """
    if indicator_max_scores is None:
        indicator_max_scores = {}
    
    dimension_scores = {}
    
    for dim_key, dim_info in SCORING_DIMENSIONS.items():
        all_indicators = dim_info["indicators"]
        
        # 确定该维度下实际需要计算的指标（启用且已评分）
        active_indicators = []
        for ind in all_indicators:
            # 检查是否启用
            if enabled_indicators is not None and ind not in enabled_indicators:
                continue
            # 检查是否有评分
            if ind not in indicator_scores or indicator_scores[ind] is None:
                continue
            active_indicators.append(ind)
        
        if not active_indicators:
            # 该维度没有任何指标被启用或评分
            dimension_scores[dim_key] = 0.0
            continue
        
        # 计算该维度下所有启用指标的总得分和总满分
        dim_actual = 0.0
        dim_max = 0.0
        
        for ind in active_indicators:
            dim_actual += indicator_scores[ind]
            # 使用传入的满分，如果没有则默认10分
            dim_max += indicator_max_scores.get(ind, 10)
        
        # 计算百分制得分
        if dim_max > 0:
            dimension_scores[dim_key] = round((dim_actual / dim_max) * 100, 2)
        else:
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
    """
    计算加权总分
    只对已评分的维度加权，未评分的维度不参与计算
    """
    if weights is None:
        weights = {dim: info["weight"] for dim, info in SCORING_DIMENSIONS.items()}
    
    total = 0.0
    total_weight = 0.0
    
    for dim_key, score in dimension_scores.items():
        # 只计算有分数（>0）的维度
        if score > 0:
            weight = weights.get(dim_key, 0)
            total += score * weight
            total_weight += weight
    
    if total_weight > 0:
        return round(total / total_weight, 2)
    return 0.0