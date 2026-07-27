"""
API 路由注册
"""

from fastapi import APIRouter

from backend.api import auth, users, tasks, submissions, review, profile, export, term_scores, rubric
from backend.api.scores import router as scores_router


print("✅ 正在导入 profile 路由...")
api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tasks.router)
api_router.include_router(submissions.router)
api_router.include_router(review.router)
api_router.include_router(profile.router)
api_router.include_router(export.router)
api_router.include_router(term_scores.router)
api_router.include_router(rubric.router)
api_router.include_router(scores_router)

__all__ = ["api_router"]