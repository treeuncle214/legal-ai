"""
用户、班级、学生-班级关联模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.database.engine import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # ========== 🆕 新增字段 ==========
    college = Column(String(100), nullable=True)   # 学院
    major = Column(String(100), nullable=True)     # 专业

    # 关系：教师管理的班级
    managed_classes = relationship("Class", back_populates="teacher", foreign_keys="Class.teacher_id")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "display_name": self.display_name or self.username,
            "college": self.college or "",      # 🆕
            "major": self.major or "",          # 🆕
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class Class(Base):
    """班级表"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, nullable=True)  # 预留：未来课程扩展
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    teacher = relationship("User", back_populates="managed_classes", foreign_keys=[teacher_id])
    students = relationship("UserClass", back_populates="class_ref")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.display_name if self.teacher else None,
            "course_id": self.course_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "student_count": len(self.students) if self.students else 0
        }


class UserClass(Base):
    """学生-班级关联表"""
    __tablename__ = "user_class"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.now)

    # 关系
    user = relationship("User")
    class_ref = relationship("Class", back_populates="students")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "class_id": self.class_id,
            "joined_at": self.joined_at.strftime("%Y-%m-%d %H:%M:%S") if self.joined_at else None
        }