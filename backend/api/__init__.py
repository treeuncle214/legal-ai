"""
API 路由注册
"""

from fastapi import APIRouter

# 添加 rubric 到导入列表
from backend.api import auth, users, tasks, submissions, review, profile, export, term_scores, rubric

# 创建主路由
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tasks.router)
api_router.include_router(submissions.router)
api_router.include_router(review.router)
api_router.include_router(profile.router)
api_router.include_router(export.router)
api_router.include_router(term_scores.router)
api_router.include_router(rubric.router)  # ← 添加这一行

# 确保导出 api_router
__all__ = ["api_router"]