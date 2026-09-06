# backend/core/prompts/__init__.py
"""
AI 提示词构建模块
"""

from .templates import INDICATOR_NAMES, INDICATOR_RUBRIC, get_indicator_name, get_indicator_rubric
from .exercise_prompt import build_exercise_prompt, get_document_focus_indicators

__all__ = [
    "INDICATOR_NAMES",
    "INDICATOR_RUBRIC",
    "get_indicator_name",
    "get_indicator_rubric",
    "build_exercise_prompt",
    "get_document_focus_indicators",
]