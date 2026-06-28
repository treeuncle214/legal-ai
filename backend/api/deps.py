# backend/api/deps.py
"""
API 依赖注入
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Generator, List, Optional

from backend.database import SessionLocal
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


# ==================== 班级相关依赖 ====================

def get_student_class_id(current_user: dict = Depends(get_current_student)) -> int:
    """
    获取当前学生所属的班级ID
    如果一个学生属于多个班级，返回第一个（业务上应限制唯一）
    """
    from backend.database.engine import get_db_connection
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT class_id FROM user_class 
            WHERE user_id = (SELECT id FROM users WHERE username = ?)
            LIMIT 1
        """, (current_user["username"],))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="学生未分配到任何班级")
        return row[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取班级信息失败: {e}")
    finally:
        conn.close()


def get_teacher_class_ids(current_user: dict = Depends(get_current_teacher)) -> List[int]:
    """
    获取当前教师负责的所有班级ID列表
    """
    from backend.database.engine import get_db_connection
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM classes 
            WHERE teacher_id = (SELECT id FROM users WHERE username = ?)
        """, (current_user["username"],))
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取班级列表失败: {e}")
    finally:
        conn.close()


def get_user_id_by_username(username: str) -> int:
    """根据用户名获取用户ID"""
    from backend.database.engine import get_db_connection
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"用户不存在: {username}")
        return row[0]
    finally:
        conn.close()