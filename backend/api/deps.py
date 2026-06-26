# backend/api/deps.py
"""
API 依赖注入
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Generator

from backend.database import SessionLocal  # 添加这一行
from backend.database import get_user
from backend.core.auth import verify_token

security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前登录用户（学生或教师）"""
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    user = get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="用户不存在"
        )
    
    return user


def get_current_teacher(current_user: dict = Depends(get_current_user)):
    """获取当前教师用户（学生不可访问）"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="仅教师可访问")
    return current_user


def get_current_student(current_user: dict = Depends(get_current_user)):
    """获取当前学生用户"""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="仅学生可访问")
    return current_user