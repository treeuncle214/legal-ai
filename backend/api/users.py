# backend/api/users.py
"""
用户管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db, get_current_teacher, get_current_user,get_teacher_class_ids
from backend.database import (
    add_user, get_all_students, get_all_users, delete_user,
    get_user_by_id, get_user
)
from backend.database.classes import (
    create_class, get_class, get_teacher_classes, get_class_students,
    add_student_to_class, remove_student_from_class, delete_class
)
from backend.database.models import User
from backend.schemas.user import UserCreate, UserResponse
from backend.schemas.common import Response
from backend.core.auth import verify_password, get_password_hash  # 导入密码函数

router = APIRouter(prefix="/api", tags=["用户管理"])


# ==================== 用户管理接口 ====================

@router.get("/users", response_model=Response[list])
async def get_users(
    role: str = None,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取用户列表
    - admin：看所有用户
    - 普通教师：只看自己班级的学生
    """
    from backend.database.engine import get_db_connection
    
    # 如果是 admin，返回所有用户
    if current_user["username"] == "admin":
        query = db.query(User)
        if role == "student":
            query = query.filter(User.role == 'student')
        elif role == "teacher":
            query = query.filter(User.role == 'teacher')
        users = query.all()
        return Response(data=[u.to_dict() for u in users])
    
    # 普通教师：只返回自己班级的学生
    teacher_class_ids = get_teacher_class_ids(current_user)
    if not teacher_class_ids:
        return Response(data=[])
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        placeholder = ','.join('?' * len(teacher_class_ids))
        cursor.execute(f"""
            SELECT DISTINCT u.* 
            FROM users u
            JOIN user_class uc ON u.id = uc.user_id
            WHERE uc.class_id IN ({placeholder})
            AND u.role = 'student'
            ORDER BY u.username
        """, teacher_class_ids)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        students = [dict(zip(columns, row)) for row in rows]
        return Response(data=students)
    finally:
        conn.close()


@router.post("/users", response_model=Response)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """添加单个用户"""
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
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


# ==================== 班级管理接口 ====================

@router.get("/classes", response_model=Response[list])
async def get_classes(
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取当前教师的所有班级"""
    from backend.database import get_user
    teacher = get_user(current_user["username"])
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    classes = get_teacher_classes(teacher["id"])
    return Response(data=classes)


@router.post("/classes", response_model=Response)
async def create_class_api(
    name: str,  # 从查询参数获取
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """创建班级"""
    from backend.database import get_user
    teacher = get_user(current_user["username"])
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="班级名称不能为空")
    
    class_id = create_class(name.strip(), teacher["id"])
    return Response(data={"id": class_id}, message=f"班级 '{name}' 创建成功")

@router.get("/classes/{class_id}/students", response_model=Response[list])
async def get_class_students_api(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """获取班级学生列表"""
    # 验证班级属于当前教师
    from backend.api.deps import get_teacher_class_ids
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权查看此班级")
    
    students = get_class_students(class_id)
    return Response(data=students)


@router.post("/classes/{class_id}/students", response_model=Response)
async def add_student_to_class_api(
    class_id: int,
    username: str,  # 从查询参数获取
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """向班级添加学生"""
    # 验证班级属于当前教师
    from backend.api.deps import get_teacher_class_ids
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    user = get_user(username)
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user["role"] != "student":
        raise HTTPException(status_code=400, detail="该用户不是学生")
    
    success = add_student_to_class(user["id"], class_id)
    if not success:
        raise HTTPException(status_code=400, detail="该学生已在班级中")
    
    return Response(message=f"学生 {username} 已加入班级")


@router.delete("/classes/{class_id}/students/{username}", response_model=Response)
async def remove_student_from_class_api(
    class_id: int,
    username: str,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """从班级移除学生"""
    from backend.api.deps import get_teacher_class_ids
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    success = remove_student_from_class(user["id"], class_id)
    if not success:
        raise HTTPException(status_code=400, detail="该学生不在班级中")
    
    return Response(message=f"学生 {username} 已从班级移除")


@router.delete("/classes/{class_id}", response_model=Response)
async def delete_class_api(
    class_id: int,
    current_user: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """删除班级（仅当无学生时）"""
    from backend.api.deps import get_teacher_class_ids
    teacher_class_ids = get_teacher_class_ids(current_user)
    if class_id not in teacher_class_ids:
        raise HTTPException(status_code=403, detail="无权操作此班级")
    
    success = delete_class(class_id)
    if not success:
        raise HTTPException(status_code=400, detail="班级中还有学生，无法删除")
    
    return Response(message="班级删除成功")


# ==================== 修改密码接口 ====================

@router.put("/users/password", response_model=Response)
async def change_password(
    password_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改当前用户密码"""
    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请提供旧密码和新密码")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6位")
    
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    
    user.password = get_password_hash(new_password)
    db.commit()
    
    return Response(message="密码修改成功")