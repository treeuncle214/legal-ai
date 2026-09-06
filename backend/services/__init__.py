"""
服务层模块 - 处理复杂业务逻辑
"""

from backend.services.word_exporter import export_report_to_word

__all__ = [
    "export_report_to_word"
]
