# backend/core/clients/__init__.py
"""
AI API 客户端模块
"""

from .deepseek_client import call_deepseek_api, test_api, OPENAI_AVAILABLE

__all__ = [
    "call_deepseek_api",
    "test_api",
    "OPENAI_AVAILABLE",
]