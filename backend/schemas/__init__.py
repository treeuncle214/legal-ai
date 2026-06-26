"""
Pydantic 模型统一导出
"""

from backend.schemas.common import (
    Response,
    PaginatedResponse,
    LoginRequest,
    LoginResponse,
    HealthResponse
)

from backend.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    BatchUsersRequest,
    BatchUsersResponse
)

from backend.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse
)

from backend.schemas.submission import (
    TextSubmissionRequest,
    WordSubmissionRequest,
    ReviewRequest,
    SubmissionResponse,
    ScoreResult,
    AIScoreResponse
)

from backend.schemas.profile import (
    DimensionScore,
    DimensionProfile,
    ProfileResponse,
    DimensionConfigResponse
)

__all__ = [
    # common
    "Response",
    "PaginatedResponse", 
    "LoginRequest",
    "LoginResponse",
    "HealthResponse",
    # user
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "BatchUsersRequest",
    "BatchUsersResponse",
    # task
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    # submission
    "TextSubmissionRequest",
    "WordSubmissionRequest", 
    "ReviewRequest",
    "SubmissionResponse",
    "ScoreResult",
    "AIScoreResponse",
    # profile
    "DimensionScore",
    "DimensionProfile",
    "ProfileResponse",
    "DimensionConfigResponse"
]