# backend/api/users.py
"""
用户管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher
from backend.database import add_user, get_all_students, get_all_users, delete_user
from backend.database.models import User  # 添加这一行
from backend.schemas.user import UserCreate, UserResponse
from backend.schemas.common import Response

router = APIRouter(prefix="/api", tags=["用户管理"])


@router.get("/users", response_model=Response[list])
async def get_users(
    role: str = None,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取用户列表（教师专用）"""
    if role == "student":
        # 确保只返回 role 为 student 的用户
        users = db.query(User).filter(User.role == 'student').all()
    elif role == "teacher":
        users = db.query(User).filter(User.role == 'teacher').all()
    else:
        users = db.query(User).all()
    
    # 转换为字典列表
    result = [u.to_dict() for u in users]
    return Response(data=result)


@router.post("/users", response_model=Response)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """添加单个用户"""
    # 检查用户是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    add_user(
        username=user_data.username,
        password=user_data.password,
        role=user_data.role,
        display_name=user_data.display_name
    )
    return Response(message="用户添加成功")


@router.post("/users", response_model=Response)
async def create_user(
    user_data: UserCreate,  # 确保 UserCreate 包含 role 字段
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """添加单个用户"""
    # 检查用户是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 确保角色正确，默认为 student，但允许 teacher
    role = user_data.role if user_data.role in ["student", "teacher"] else "student"
    
    add_user(
        username=user_data.username,
        password=user_data.password,
        role=role,
        display_name=user_data.display_name or user_data.username
    )
    return Response(message="用户添加成功")


@router.delete("/users/{username}", response_model=Response)
async def remove_user(
    username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """删除用户"""
    if username == current_user["username"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    delete_user(username)
    return Response(message="用户删除成功")