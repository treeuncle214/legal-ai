# backend/api/__init__.py
"""
API 路由注册
"""

from fastapi import APIRouter

from backend.api import auth, users, tasks, submissions, review, profile, export

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

# 确保导出 api_router
__all__ = ["api_router"]