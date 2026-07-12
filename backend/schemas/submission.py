# backend/schemas/submission.py
"""
提交相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class TextSubmissionRequest(BaseModel):
    """文本提交请求（已废弃，仅保留兼容）"""
    task_id: int
    process_log: str = ""
    ai_interaction_log: str = ""
    final_output: str = ""
    tools_used: List[str] = []


class WordSubmissionRequest(BaseModel):
    """Word提交请求"""
    task_id: int
    content: str  # Base64 编码的文件内容或直接文本
    filename: str


class ReviewRequest(BaseModel):
    """审批请求"""
    scores: Dict[str, float]  # {"ai_retrieval": 85, "critical": 78, ...}
    teacher_comment: str = ""


class ScoreResult(BaseModel):
    """评分结果"""
    dimension_scores: Dict[str, float]
    dimension_levels: Dict[str, str]
    ai_comment: str


class AIScoreResponse(BaseModel):
    """AI评分响应（教师端内部使用）"""
    submission_id: int
    scores: Dict[str, float]
    levels: Dict[str, str]
    weighted_total: float
    ai_comment: str
    metadata: Optional[Dict[str, Any]] = None


class SubmissionResponse(BaseModel):
    """提交记录响应（完整版，仅教师端使用）"""
    id: int
    task_id: int
    task_title: Optional[str]
    student_username: str
    submit_type: str
    submit_time: Optional[str]
    is_reviewed: int
    scores: Dict[str, float]
    levels: Dict[str, str]
    weighted_total: float
    ai_comment: Optional[str]
    teacher_comment: Optional[str]
    final_output: Optional[str]
    process_log: Optional[str]
    ai_interaction_log: Optional[str]
    word_file_path: Optional[str] = None
    word_content: Optional[str] = None
    tools_used: Optional[str] = None
    score_published: int = 0  # 0=未发布，1=已发布


class StudentSubmissionResponse(BaseModel):
    """
    学生端“我的提交”页面使用的提交记录（不含评分）
    """
    id: int
    task_id: int
    task_title: Optional[str] = None
    submit_type: str
    submit_time: Optional[str] = None
    is_reviewed: int  # 0=待审批，1=已审批
    score_published: int  # 0=未发布，1=已发布
    # 提交内容（只显示文本预览，不包含评分）
    process_log: Optional[str] = None
    final_output: Optional[str] = None
    word_file_path: Optional[str] = None
    word_content: Optional[str] = None


class PublishedScoreResponse(BaseModel):
    """
    学生端“成绩总结”页面使用的已发布成绩
    注意：不出现任何"AI"字样，统一称为"教师评分"
    """
    id: int
    task_id: int
    task_title: str
    weighted_total: float  # 总分
    teacher_comment: Optional[str] = ""  # 教师评语
    submit_time: Optional[str] = None
    is_reviewed: int = 1


class PublishResponse(BaseModel):
    """发布成绩响应"""
    submission_id: int
    published: bool
    message: str


class IndicatorScoreDetail(BaseModel):
    """单个指标的评分详情"""
    indicator_key: str
    score: float
    level: str
    comment: Optional[str] = None


class SubmissionScoreDetailResponse(BaseModel):
    """提交评分详情响应"""
    submission_id: int
    task_title: str
    total_score: float
    dimension_scores: Dict[str, float]
    dimension_levels: Dict[str, str]
    indicator_scores: List[IndicatorScoreDetail]
    ai_comment: str
    teacher_comment: Optional[str] = None
    score_published: int