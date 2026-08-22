"""
班级-教师关联模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.database.engine import Base


class ClassTeacher(Base):
    """班级-教师关联表（一个班级可以有多个教师）"""
    __tablename__ = "class_teachers"
    __table_args__ = (UniqueConstraint('class_id', 'teacher_id', name='uq_class_teacher'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(String(100), nullable=True)  # 添加者用户名
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    class_ref = relationship("Class")
    teacher = relationship("User", foreign_keys=[teacher_id])

    def to_dict(self):
        return {
            "id": self.id,
            "class_id": self.class_id,
            "teacher_id": self.teacher_id,
            "teacher_username": self.teacher.username if self.teacher else None,
            "teacher_name": self.teacher.display_name if self.teacher else None,
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }