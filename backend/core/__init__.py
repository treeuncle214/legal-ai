# backend/core/__init__.py
"""
核心业务逻辑模块
"""

from backend.core.auth import (
    verify_password,
    get_password_hash,
    authenticate_user,
    create_access_token,
    verify_token
)

# 从 scorer 导入，并提供默认值以防止导入错误
try:
    from backend.core.scorer import (
        score_submission,
        score_exercise,
        score_final_report,
        GRADE_TO_SCORE as LEVEL_TO_SCORE,
        INDICATOR_RUBRIC,
        FINAL_REPORT_MODULES,
        SCORING_DIMENSIONS
    )
except ImportError as e:
    print(f"警告: scorer 模块导入失败: {e}")
    # 提供默认实现
    def score_submission(task, submission):
        return {"dimension_scores": {}, "comment": "评分服务不可用"}
    
    def score_exercise(task, submission):
        return {"dimension_scores": {}, "comment": "评分服务不可用"}
    
    def score_final_report(task, content):
        return {"dimension_scores": {}, "comment": "评分服务不可用"}
    
    LEVEL_TO_SCORE = {"A": 100, "B": 80, "C": 60, "D": 40}
    INDICATOR_RUBRIC = {}
    FINAL_REPORT_MODULES = []
    SCORING_DIMENSIONS = {}

__all__ = [
    "verify_password",
    "get_password_hash", 
    "authenticate_user",
    "create_access_token",
    "verify_token",
    "score_submission",
    "score_exercise",
    "score_final_report",
    "LEVEL_TO_SCORE",
    "INDICATOR_RUBRIC",
    "FINAL_REPORT_MODULES",
    "SCORING_DIMENSIONS"
]