# backend/database/users.py
"""
用户 CRUD 操作
"""

from sqlalchemy.orm import Session
from backend.database.engine import SessionLocal
from backend.database.models import User


def add_user(username, password, role="student", display_name=None):
    db = SessionLocal()
    try:
        user = User(
            username=username,
            password=password,
            role=role,
            display_name=display_name or username
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def get_user(username):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user.to_dict() if user else None
    finally:
        db.close()


def get_user_by_id(user_id: int):
    """根据ID获取用户"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.to_dict() if user else None
    finally:
        db.close()


def get_user_by_session(db: Session, username: str):
    """使用已有会话获取用户（用于事务内）"""
    return db.query(User).filter(User.username == username).first()


def get_all_students():
    db = SessionLocal()
    try:
        students = db.query(User).filter(User.role == 'student').all()
        return [s.to_dict() for s in students]
    finally:
        db.close()


def get_all_users():
    """获取所有用户（包括教师和学生）"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [u.to_dict() for u in users]
    finally:
        db.close()


def delete_user(username):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_all_teachers():
    """获取所有教师用户（用于模板共享选择）"""
    db = SessionLocal()
    try:
        teachers = db.query(User).filter(User.role == "teacher").all()
        return [{"username": t.username, "display_name": t.display_name or t.username} for t in teachers]
    finally:
        db.close()