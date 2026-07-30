"""
学期总评模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime

from backend.database.engine import Base


class TermScore(Base):
    """学期总评表 - 学期结束时计算快照"""
    __tablename__ = "term_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_username = Column(String(100), nullable=False, index=True)
    
    class_id = Column(Integer, nullable=True)
    course_total_score = Column(Float, nullable=True)
    level = Column(String(20), default="待评测")
    
    # 详细提交记录（JSON字符串）
    details = Column(Text, nullable=True)
    
    A_ai_retrieval_score = Column(Float, nullable=True)
    B_critical_score = Column(Float, nullable=True)
    C_ethics_score = Column(Float, nullable=True)
    D_integration_score = Column(Float, nullable=True)
    
    A_ai_retrieval_level = Column(String(10), nullable=True)
    B_critical_level = Column(String(10), nullable=True)
    C_ethics_level = Column(String(10), nullable=True)
    D_integration_level = Column(String(10), nullable=True)
    
    A1_score = Column(Float, nullable=True)
    A2_score = Column(Float, nullable=True)
    A3_score = Column(Float, nullable=True)
    A4_score = Column(Float, nullable=True)
    B1_score = Column(Float, nullable=True)
    B2_score = Column(Float, nullable=True)
    B3_score = Column(Float, nullable=True)
    C1_score = Column(Float, nullable=True)
    C2_score = Column(Float, nullable=True)
    C3_score = Column(Float, nullable=True)
    D1_score = Column(Float, nullable=True)
    D2_score = Column(Float, nullable=True)
    D3_score = Column(Float, nullable=True)
    
    A1_level = Column(String(10), nullable=True)
    A2_level = Column(String(10), nullable=True)
    A3_level = Column(String(10), nullable=True)
    A4_level = Column(String(10), nullable=True)
    B1_level = Column(String(10), nullable=True)
    B2_level = Column(String(10), nullable=True)
    B3_level = Column(String(10), nullable=True)
    C1_level = Column(String(10), nullable=True)
    C2_level = Column(String(10), nullable=True)
    C3_level = Column(String(10), nullable=True)
    D1_level = Column(String(10), nullable=True)
    D2_level = Column(String(10), nullable=True)
    D3_level = Column(String(10), nullable=True)
    
    exercise_count = Column(Integer, default=0)
    practice_count = Column(Integer, default=0)
    final_count = Column(Integer, default=0)
    
    teacher_summary = Column(Text, nullable=True)
    
    generated_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_username": self.student_username,
            "class_id": self.class_id,
            "course_total_score": self.course_total_score,
            "level": self.level,
            "details": self.details,
            "A_ai_retrieval_score": self.A_ai_retrieval_score,
            "B_critical_score": self.B_critical_score,
            "C_ethics_score": self.C_ethics_score,
            "D_integration_score": self.D_integration_score,
            "A_ai_retrieval_level": self.A_ai_retrieval_level,
            "B_critical_level": self.B_critical_level,
            "C_ethics_level": self.C_ethics_level,
            "D_integration_level": self.D_integration_level,
            "exercise_count": self.exercise_count,
            "practice_count": self.practice_count,
            "final_count": self.final_count,
            "teacher_summary": self.teacher_summary,
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S") if self.generated_at else None
        }