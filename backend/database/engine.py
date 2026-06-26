"""
数据库引擎和会话管理
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import DB_PATH
from sqlite3 import connect, Connection
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# 数据库文件路径
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./data/assessment.db").replace("sqlite:///", "")

def get_db_connection() -> Connection:
    """获取数据库连接"""
    # 确保 data 目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return connect(DB_PATH)


@contextmanager
def get_db():
    """上下文管理器方式的数据库连接"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
# 根据环境变量选择数据库
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{DB_PATH}"
)

# SQLite 需要特殊配置
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_session():
    """FastAPI 依赖注入使用"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    """获取数据库会话（兼容旧代码）"""
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise