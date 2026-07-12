"""
等级映射工具
"""

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
    """等级转分数（用于兼容）"""
    level_map = {"优": 88, "良": 78, "合格": 65, "不合格": 45}
    return level_map.get(level, 60)


def grade_to_score(grade: str) -> float:
    """等级转分数（兼容旧接口）"""
    return level_to_score(grade)


# 保持向后兼容
GRADE_TO_SCORE = {"A": 88, "B": 78, "C": 65, "D": 45}