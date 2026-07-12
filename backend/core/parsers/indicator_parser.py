"""
指标评分解析器
"""
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

VALID_INDICATORS = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "D3"]

def parse_indicator_scores(ai_response: Dict) -> Dict:
    """
    解析AI返回的指标评分
    """
    result = {
        "indicator_scores": {},
        "indicator_levels": {},
        "indicator_comments": {},
        "overall_comment": ""
    }
    
    if "indicators" in ai_response:
        for item in ai_response["indicators"]:
            key = item.get("key")
            score = item.get("score")
            comment = item.get("comment", "")
            
            # ✅ 验证指标代码是否有效
            if key and score is not None:
                # 如果指标代码不是标准格式，尝试修正
                if key not in VALID_INDICATORS:
                    # 尝试将 A5 -> A1, A6 -> A2 等映射（但最好在Prompt中避免）
                    # 这里打印警告并跳过无效指标
                    print(f"⚠️ 警告: 无效指标代码 '{key}'，已跳过")
                    continue
                
                result["indicator_scores"][key] = float(score)
                result["indicator_levels"][key] = score_to_level(score)
                result["indicator_comments"][key] = comment
        
        result["overall_comment"] = ai_response.get("overall_comment", "")
    else:
        # 兼容旧格式
        scores = ai_response.get("indicator_scores", {})
        comments = ai_response.get("indicator_comments", {})
        
        for key, score in scores.items():
            if key in VALID_INDICATORS:
                if isinstance(score, str):
                    score = level_to_score(score)
                result["indicator_scores"][key] = float(score)
                result["indicator_levels"][key] = score_to_level(score)
                result["indicator_comments"][key] = comments.get(key, f"{score}分")
            else:
                print(f"⚠️ 警告: 无效指标代码 '{key}'，已跳过")
        
        result["overall_comment"] = ai_response.get("comment", "")
    
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


def level_to_score(level: str) -> float:
    """等级转分数（用于兼容旧格式）"""
    level_map = {"A": 88, "B": 78, "C": 65, "D": 45}
    return level_map.get(level.upper(), 60)


def get_all_indicators() -> List[str]:
    """获取所有13个指标"""
    return ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "D3"]