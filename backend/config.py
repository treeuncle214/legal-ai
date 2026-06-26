"""
全局配置
集中管理评分维度、API设置等，方便后续扩展

评分体系：
- 4大一级维度（核心能力）
- 14个二级指标（可观测的能力点）
- 期末报告按8模块/100分制评分，自动映射到4维度
- 平时练习按启用指标评A/B/C/D等级
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========== 路径配置（支持环境变量，方便部署） ==========

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据目录（可通过环境变量覆盖，用于生产环境）
DATA_DIR = os.getenv("DATA_DIR", str(BASE_DIR / "data"))
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
EXPORT_DIR = os.path.join(DATA_DIR, "exports")
TEMP_DIR = os.path.join(DATA_DIR, "temp")
LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))

# 数据库路径
DB_PATH = os.path.join(DATA_DIR, "assessment.db")

# 确保必要目录存在
for dir_path in [DATA_DIR, UPLOAD_DIR, EXPORT_DIR, TEMP_DIR, LOG_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ========== 文件上传限制 ==========
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 10))  # 默认10MB
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FILE_EXTENSIONS = [".docx"]

# 文件保留天数（超过此天数的文件会被自动清理）
FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", 30))

# 存储空间限制（MB）
MAX_STORAGE_MB = int(os.getenv("MAX_STORAGE_MB", 500))

# ========== 评分维度定义 ==========
SCORING_DIMENSIONS = [
    {
        "key": "ai_retrieval",
        "name": "AI融合智能检索能力",
        "weight": 0.30,
        "sub_indicators": [
            {"key": "A1", "name": "问题拆解与检索目标设定",
             "description": "能准确拆解复杂法律问题为可检索的子问题，明确检索目标与范围"},
            {"key": "A2", "name": "检索策略设计",
             "description": "合理选择关键词（含同义词、上位/下位词）、数据库/平台、检索方法"},
            {"key": "A3", "name": "AI工具融合应用",
             "description": "能有效使用AI工具辅助检索（提问、生成、调整、核验），并记录过程"},
            {"key": "A4", "name": "检索策略优化",
             "description": "能根据初步结果调整策略，提升查全率与查准率"},
        ]
    },
    {
        "key": "critical",
        "name": "批判性评估能力",
        "weight": 0.20,
        "sub_indicators": [
            {"key": "B1", "name": "信息来源评估",
             "description": "能对检索结果从权威性、时效性、相关性、客观性进行评估"},
            {"key": "B2", "name": "AI内容验证",
             "description": "能识别AI生成内容的错误、遗漏或偏见，并通过人工核验纠正"},
            {"key": "B3", "name": "争议与分歧分析",
             "description": "能比较不同来源的立场差异，做出合理判断"},
        ]
    },
    {
        "key": "ethics",
        "name": "伦理合规辨识能力",
        "weight": 0.20,
        "sub_indicators": [
            {"key": "C1", "name": "信息隐私与合法边界",
             "description": "能识别检索及使用信息中的隐私侵犯、非法获取等问题并提出处理方式"},
            {"key": "C2", "name": "算法偏见与公平意识",
             "description": "能识别AI工具或数据源可能存在的偏见及其对结论的影响"},
            {"key": "C3", "name": "职业伦理与责任意识",
             "description": "能反思自身作为信息检索者的职业道德（如披露义务、避免误导、勤勉核验）"},
        ]
    },
    {
        "key": "integration",
        "name": "信息整合应用能力",
        "weight": 0.30,
        "sub_indicators": [
            {"key": "D1", "name": "信息分类与组织",
             "description": "能将检索结果按类型、可信度分级整理，形成结构化表格或摘要"},
            {"key": "D2", "name": "综合分析能力",
             "description": "能整合多源信息回答子问题，处理开放性问题并给出合理建议"},
            {"key": "D3", "name": "实用成果产出",
             "description": "能生成解决实际问题的操作指南、法律意见、证据清单等实用文档"},
            {"key": "D4", "name": "自我反思与局限认知",
             "description": "能评价检索过程的局限性、AI辅助的利弊，并提出改进方向"},
        ]
    },
]

# ========== 辅助函数 ==========

def get_dimension_keys():
    """获取所有维度key"""
    return [d["key"] for d in SCORING_DIMENSIONS]


def get_dimension_name(key):
    """根据维度key获取中文名称"""
    for d in SCORING_DIMENSIONS:
        if d["key"] == key:
            return d["name"]
    return key


def get_dimension_weight(key):
    """根据维度key获取权重"""
    for d in SCORING_DIMENSIONS:
        if d["key"] == key:
            return d.get("weight", 0.25)
    return 0.25


# 14个二级指标的扁平列表
INDICATORS = []
for dim in SCORING_DIMENSIONS:
    for ind in dim.get("sub_indicators", []):
        INDICATORS.append({
            "key": ind["key"],
            "name": ind["name"],
            "dimension": dim["key"],
            "description": ind.get("description", "")
        })


def get_indicator_to_dimension_map():
    """获取二级指标key到维度key的映射"""
    mapping = {}
    for ind in INDICATORS:
        mapping[ind["key"]] = ind["dimension"]
    return mapping


def get_final_report_module_mapping():
    """期末报告8模块映射"""
    return [
        {"module": "问题拆解与检索目标", "max_score": 10, "dimension_key": "ai_retrieval"},
        {"module": "检索策略与过程记录", "max_score": 20, "dimension_key": "ai_retrieval"},
        {"module": "信息批判性评估",     "max_score": 15, "dimension_key": "critical"},
        {"module": "伦理与合规分析",     "max_score": 15, "dimension_key": "ethics"},
        {"module": "检索结果分类呈现",   "max_score": 10, "dimension_key": "integration"},
        {"module": "综合分析与结论",     "max_score": 15, "dimension_key": "integration"},
        {"module": "检索局限性与自我评价","max_score": 5,  "dimension_key": "integration"},
        {"module": "报告整体质量与附件", "max_score": 10, "dimension_key": "integration"},
    ]


# ========== AI API 配置 ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# AI 请求超时时间（秒）
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", 60))

# ========== 数据库配置 ==========
# 支持 SQLite（开发）和 PostgreSQL（生产）
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# ========== 应用信息 ==========
APP_NAME = "法律信息智能检索 - AI能力测评系统"
APP_VERSION = "2.0.0"

# ========== 安全配置 ==========
# JWT 密钥（生产环境必须修改）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 默认24小时
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# ========== CORS 配置 ==========
# 允许的跨域来源（生产环境设置具体域名）
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")