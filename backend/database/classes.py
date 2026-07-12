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
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            return []
        
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


def get_student_class_info(username: str) -> Optional[Dict]:
    """获取学生当前的班级信息（用于检查是否已在其他班级）"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username, User.role == 'student').first()
        if not user:
            return None
        
        user_class = db.query(UserClass).filter(UserClass.user_id == user.id).first()
        if not user_class:
            return None
        
        class_obj = db.query(Class).filter(Class.id == user_class.class_id).first()
        if not class_obj:
            return None
        
        return {
            "class_id": class_obj.id,
            "class_name": class_obj.name,
            "teacher_id": class_obj.teacher_id
        }
    finally:
        db.close()


def check_student_in_any_class(user_id: int) -> Optional[int]:
    """检查学生是否已在某个班级，返回班级ID，如果没有则返回None"""
    db = SessionLocal()
    try:
        user_class = db.query(UserClass).filter(UserClass.user_id == user_id).first()
        if user_class:
            return user_class.class_id
        return None
    finally:
        db.close()


def add_student_to_class(user_id: int, class_id: int) -> Dict:
    """
    将学生添加到班级
    返回: {"success": bool, "message": str, "existing_class_id": int|None}
    """
    db = SessionLocal()
    try:
        # 1. 验证用户存在且是学生
        user = db.query(User).filter(User.id == user_id, User.role == 'student').first()
        if not user:
            return {"success": False, "message": "用户不存在或不是学生", "existing_class_id": None}
        
        # 2. 验证班级存在
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            return {"success": False, "message": "班级不存在", "existing_class_id": None}
        
        # 3. 检查是否已在当前班级
        existing = db.query(UserClass).filter(
            UserClass.user_id == user_id,
            UserClass.class_id == class_id
        ).first()
        if existing:
            return {"success": False, "message": f"该学生已在当前班级中", "existing_class_id": class_id}
        
        # 4. 检查是否已在其他班级
        other_class = db.query(UserClass).filter(UserClass.user_id == user_id).first()
        if other_class:
            other_class_obj = db.query(Class).filter(Class.id == other_class.class_id).first()
            class_name = other_class_obj.name if other_class_obj else f"ID={other_class.class_id}"
            return {
                "success": False, 
                "message": f"该学生已在「{class_name}」班级中，如需更换请先从原班级移除",
                "existing_class_id": other_class.class_id
            }
        
        # 5. 添加学生到班级
        user_class = UserClass(user_id=user_id, class_id=class_id)
        db.add(user_class)
        db.commit()
        return {"success": True, "message": "添加成功", "existing_class_id": None}
    except Exception as e:
        db.rollback()
        print(f"添加学生到班级失败: {e}")
        return {"success": False, "message": f"添加失败: {str(e)}", "existing_class_id": None}
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


# ==================== 新增：按名称查找班级 ====================

def find_class_by_name(class_name: str, teacher_id: Optional[int] = None) -> Optional[Dict]:
    """
    按班级名称查找班级
    如果指定 teacher_id，则只查找该教师名下的班级
    """
    db = SessionLocal()
    try:
        query = db.query(Class).filter(Class.name == class_name)
        if teacher_id is not None:
            query = query.filter(Class.teacher_id == teacher_id)
        class_obj = query.first()
        if not class_obj:
            return None
        return class_obj.to_dict()
    finally:
        db.close()


# ==================== 新增：获取所有教师列表（用于班级创建） ====================

def get_all_teachers_with_classes() -> List[Dict]:
    """获取所有教师及其班级数量"""
    db = SessionLocal()
    try:
        teachers = db.query(User).filter(User.role == 'teacher').all()
        result = []
        for t in teachers:
            class_count = db.query(Class).filter(Class.teacher_id == t.id).count()
            result.append({
                "id": t.id,
                "username": t.username,
                "display_name": t.display_name or t.username,
                "class_count": class_count
            })
        return result
    finally:
        db.close()