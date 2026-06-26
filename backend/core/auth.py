# backend/core/auth.py
"""
认证核心逻辑
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7天

# 使用更简单的哈希方式，避免 bcrypt 问题
def simple_hash(password: str) -> str:
    """使用 SHA-256 进行简单哈希"""
    salt = "legal-ai-salt-2024"  # 固定盐值，实际生产环境应该使用随机盐
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_simple_hash(password: str, hashed: str) -> bool:
    """验证简单哈希"""
    return simple_hash(password) == hashed

# 尝试使用 bcrypt，如果失败则使用简单哈希
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    USE_BCRYPT = True
    print("✅ 使用 bcrypt 密码加密")
except Exception as e:
    print(f"⚠️ bcrypt 不可用，使用简单哈希: {e}")
    USE_BCRYPT = False

def verify_password(plain_password, hashed_password):
    """验证密码（兼容多种方式）"""
    if not hashed_password:
        return False
    
    # 如果没有 $ 符号，说明是简单哈希或明文
    if "$" not in str(hashed_password):
        # 尝试简单哈希验证
        if verify_simple_hash(plain_password, hashed_password):
            return True
        # 兼容明文
        return plain_password == hashed_password
    
    # 使用 bcrypt 验证
    if USE_BCRYPT:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return plain_password == hashed_password
    
    return plain_password == hashed_password


def get_password_hash(password):
    """获取密码哈希"""
    if USE_BCRYPT:
        try:
            # bcrypt 限制密码长度为 72 字节
            if len(password.encode('utf-8')) > 72:
                password = password[:72]
            return pwd_context.hash(password)
        except Exception:
            return simple_hash(password)
    else:
        return simple_hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建 access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """创建 refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access"):
    """验证 token"""
    try:
        secret_key = SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.JWTError:
        return None


def refresh_access_token(refresh_token: str):
    """
    使用 refresh token 刷新 access token
    
    返回新的 access token，如果 refresh token 无效则返回 None
    """
    payload = verify_token(refresh_token, token_type="refresh")
    if payload is None:
        return None
    
    # 创建新的 access token
    new_access_token = create_access_token(
        data={"sub": payload.get("sub"), "role": payload.get("role")}
    )
    
    return new_access_token


def authenticate_user(db: Session, username: str, password: str):
    """验证用户"""
    from backend.database import get_user
    
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.get("password", "")):
        return None
    return user