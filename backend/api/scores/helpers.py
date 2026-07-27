"""
辅助函数
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from backend.database.models import Task, TaskRubricIndicator


def get_level(score: float) -> str:
    """根据得分获取等级"""
    if score >= 85:
        return "优秀"
    elif score >= 75:
        return "良好"
    elif score >= 55:
        return "合格"
    else:
        return "不合格"


def get_indicator_max_score(task_id: int, indicator_key: str, db: Session) -> int:
    """获取任务中某个指标的满分"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.task_rubric_id:
        return 10
    
    indicator = db.query(TaskRubricIndicator).filter(
        TaskRubricIndicator.task_rubric_id == task.task_rubric_id,
        TaskRubricIndicator.indicator_key == indicator_key
    ).first()
    
    return indicator.max_score if indicator else 10


def get_all_indicator_max_scores(task_id: int, db: Session) -> Dict[str, int]:
    """获取任务中所有指标的满分"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.task_rubric_id:
        return {}
    
    indicators = db.query(TaskRubricIndicator).filter(
        TaskRubricIndicator.task_rubric_id == task.task_rubric_id
    ).all()
    
    return {ind.indicator_key: ind.max_score for ind in indicators}