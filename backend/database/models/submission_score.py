"""
提交评分详情模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean

from backend.database.engine import Base


class SubmissionScore(Base):
    """提交评分详情表 - 存储每个二级指标的得分"""
    __tablename__ = "submission_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    indicator_key = Column(String(10), nullable=False)
    score = Column(Float, nullable=False)
    level = Column(String(10), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "indicator_key": self.indicator_key,
            "score": self.score,
            "level": self.level,
            "comment": self.comment,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


