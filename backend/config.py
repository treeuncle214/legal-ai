"""
全局配置
集中管理评分维度、API设置等，方便后续扩展

评分体系：
- 4大一级维度（核心能力）
- 13个二级指标（可观测的能力点）
- 所有作业类型（课堂练习/任务实践/期末考察）统一按13指标评分
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 运行环境：development / testing / production
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 日志级别（DEBUG / INFO / WARNING / ERROR）
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

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
        "sub_indicators": [
            {
                "key": "A1",
                "name": "检索目标拆解",
                "description": "能准确拆解复杂法律问题为可检索的子问题，明确检索目标与范围"
            },
            {
                "key": "A2",
                "name": "检索策略设计",
                "description": "合理选择关键词（含同义词、上位/下位词）、数据库/平台/AI工具、检索方法"
            },
            {
                "key": "A3",
                "name": "AI工具融合应用",
                "description": "能有效融入AI工具辅助检索，含提问、生成、判断、调整等"
            },
            {
                "key": "A4",
                "name": "检索策略优化",
                "description": "能根据初步结果调整策略，不断靠近最佳结果"
            },
        ]
    },
    {
        "key": "critical",
        "name": "批判性评估能力",
        "sub_indicators": [
            {
                "key": "B1",
                "name": "信息来源评估",
                "description": "能对检索结果（含AI结果）从权威性、时效性、相关性、客观性进行评估"
            },
            {
                "key": "B2",
                "name": "AI内容验证",
                "description": "能识别AI生成内容的错误、遗漏、虚假、无效或偏见，并通过人工核验纠正"
            },
            {
                "key": "B3",
                "name": "争议与分歧分析",
                "description": "能比较不同来源立场差异、观点差异、做法差异等，做出合理判断"
            },
        ]
    },
    {
        "key": "ethics",
        "name": "伦理合规辨识能力",
        "sub_indicators": [
            {
                "key": "C1",
                "name": "风险类型识别",
                "description": "能识别检索及使用信息中的各类型的伦理风险、合规风险"
            },
            {
                "key": "C2",
                "name": "价值综合判断",
                "description": "能对相关伦理与合规风险，分析风险法律依据或伦理原则，形成明确的价值判断"
            },
            {
                "key": "C3",
                "name": "风险处理方式",
                "description": "基于伦理或合规风险点，提出具体可操作的风险处理方案，体现人的主观能动性及责任主体性"
            },
        ]
    },
    {
        "key": "integration",
        "name": "信息整合应用能力",
        "sub_indicators": [
            {
                "key": "D1",
                "name": "信息分类与组织",
                "description": "能将多源检索结果按信息类型、可信度分级等整合与组织，形成结构化信息"
            },
            {
                "key": "D2",
                "name": "综合分析与决策",
                "description": "能基于多源信息进行专业分析与知识发现（比如信息挖掘、应用迁移、逻辑论证等），给出解决实际问题的方法、方案或建议"
            },
            {
                "key": "D3",
                "name": "局限反思",
                "description": "能评价检索过程的局限性、AI辅助的利弊，能提出改进方向并持续保持学习力"
            },
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


def get_level_by_score(score: float) -> str:
    """根据分数获取等级"""
    if score >= 85:
        return "优"
    elif score >= 75:
        return "良"
    elif score >= 55:
        return "合格"
    else:
        return "不合格"


# ========== AI API 配置 ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# AI 请求超时时间（秒）
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", 60))

# ========== 数据库配置 ==========
# 支持 SQLite（开发）和 PostgreSQL（生产）
# 单一来源：engine.py 从这里读取，避免 config 与 engine 各自计算导致路径不一致
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/assessment.db")

# ========== 应用信息 ==========
APP_NAME = "法律信息智能检索 - AI能力测评系统"
APP_VERSION = "2.3.0"

# ========== 安全配置 ==========
# JWT 密钥（生产环境必须修改）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 默认24小时
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# 生产环境安全检查：禁止使用默认密钥
if ENVIRONMENT == "production":
    if SECRET_KEY in ("", "your-secret-key-change-in-production") or \
            REFRESH_SECRET_KEY in ("", "your-refresh-secret-key-change-in-production"):
        raise RuntimeError(
            "生产环境必须通过环境变量设置安全的 SECRET_KEY 与 REFRESH_SECRET_KEY"
        )

# ========== CORS 配置 ==========
# 允许的跨域来源（生产环境设置具体域名）
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",") if origin.strip()]