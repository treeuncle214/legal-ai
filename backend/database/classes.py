# backend/database/classes.py
"""
班级 CRUD 操作
"""

from backend.database.engine import SessionLocal
from backend.database.models import Class, UserClass, User
from typing import List, Dict, Optional
from sqlalchemy.orm import joinedload


def create_class(name: str, teacher_id: int, course_id: Optional[int] = None) -> int:
    """创建班级"""
    db = SessionLocal()
    try:
        class_obj = Class(
            name=name,
            teacher_id=teacher_id,
            course_id=course_id
        )
        db.add(class_obj)
        db.commit()
        db.refresh(class_obj)
        return class_obj.id
    finally:
        db.close()


def get_class(class_id: int) -> Optional[Dict]:
    """获取班级详情"""
    db = SessionLocal()
    try:
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            return None
        # 计算学生数量
        student_count = db.query(UserClass).filter(UserClass.class_id == class_id).count()
        result = class_obj.to_dict()
        result["student_count"] = student_count
        return result
    finally:
        db.close()


def get_teacher_classes(teacher_id: int) -> List[Dict]:
    """获取教师的所有班级"""
    db = SessionLocal()
    try:
        classes = db.query(Class).filter(Class.teacher_id == teacher_id).all()
        result = []
        for cls in classes:
            student_count = db.query(UserClass).filter(UserClass.class_id == cls.id).count()
            data = cls.to_dict()
            data["student_count"] = student_count
            result.append(data)
        return result
    finally:
        db.close()


def get_class_students(class_id: int) -> List[Dict]:
    """获取班级的所有学生"""
    db = SessionLocal()
    try:
        # 先验证班级存在
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            return []
        
        # 获取该班级的所有学生
        students = db.query(User).join(UserClass, User.id == UserClass.user_id).filter(
            UserClass.class_id == class_id,
            User.role == 'student'
        ).all()
        
        return [s.to_dict() for s in students]
    finally:
        db.close()


def get_student_class_ids(user_id: int) -> List[int]:
    """获取学生所属的所有班级ID"""
    db = SessionLocal()
    try:
        user_class = db.query(UserClass).filter(UserClass.user_id == user_id).all()
        return [uc.class_id for uc in user_class]
    finally:
        db.close()


def add_student_to_class(user_id: int, class_id: int) -> bool:
    """将学生添加到班级（防止重复）"""
    db = SessionLocal()
    try:
        # 检查是否已存在
        existing = db.query(UserClass).filter(
            UserClass.user_id == user_id,
            UserClass.class_id == class_id
        ).first()
        if existing:
            return False
        
        # 验证用户存在且是学生
        user = db.query(User).filter(User.id == user_id, User.role == 'student').first()
        if not user:
            return False
        
        # 验证班级存在
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            return False
        
        user_class = UserClass(user_id=user_id, class_id=class_id)
        db.add(user_class)
        db.commit()
        return True
    finally:
        db.close()


def remove_student_from_class(user_id: int, class_id: int) -> bool:
    """从班级移除学生"""
    db = SessionLocal()
    try:
        user_class = db.query(UserClass).filter(
            UserClass.user_id == user_id,
            UserClass.class_id == class_id
        ).first()
        if not user_class:
            return False
        
        db.delete(user_class)
        db.commit()
        return True
    finally:
        db.close()


def delete_class(class_id: int) -> bool:
    """删除班级（只能删除没有学生的班级）"""
    db = SessionLocal()
    try:
        # 检查是否有学生
        student_count = db.query(UserClass).filter(UserClass.class_id == class_id).count()
        if student_count > 0:
            return False
        
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            return False
        
        db.delete(class_obj)
        db.commit()
        return True
    finally:
        db.close()