"""
通用辅助函数
"""

import uuid
import time
from datetime import datetime
from typing import List, TypeVar, Callable
from functools import wraps

T = TypeVar('T')


def generate_id() -> str:
    """生成唯一ID"""
    return uuid.uuid4().hex[:16]


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if dt is None:
        return ""
    return dt.strftime(fmt)


def calculate_percentage(value: float, total: float) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return round((value / total) * 100, 2)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    失败重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


def safe_get(dictionary: dict, key: str, default=None):
    """安全获取字典值（支持点号路径）"""
    keys = key.split(".")
    value = dictionary
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
    return value if value is not None else default