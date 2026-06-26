"""
认证相关 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_user
from backend.schemas.common import LoginRequest, LoginResponse, Response
from backend.core.auth import authenticate_user, create_access_token

router = APIRouter(prefix="/api", tags=["认证"])


@router.post("/login", response_model=Response[LoginResponse])
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    
    return Response(
        data=LoginResponse(
            access_token=access_token,
            username=user["username"],
            role=user["role"],
            display_name=user["display_name"]
        )
    )