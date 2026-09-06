# backend/core/auth.py
"""
认证核心逻辑
"""
import hashlib
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# 统一从 backend.config 读取密钥与有效期，避免环境变量被硬编码覆盖
from backend.config import (
    SECRET_KEY,
    REFRESH_SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# 强制使用 bcrypt（不再退化为固定盐 SHA-256 或明文）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 仅用于「识别并兼容」历史遗留的弱哈希，绝不再用于新密码
_LEGACY_SALT = "legal-ai-salt-2024"


def _legacy_hash(password: str) -> str:
    """历史遗留的固定盐 SHA-256（仅用于存量账号校验，登录成功后会自动升级）"""
    return hashlib.sha256(f"{_LEGACY_SALT}{password}".encode()).hexdigest()


def is_bcrypt_hash(hashed) -> bool:
    """判断是否为 bcrypt 哈希（以 $2a$/$2b$/$2y$ 开头）"""
    return bool(hashed) and str(hashed).startswith(("$2a$", "$2b$", "$2y$"))


def get_password_hash(password: str) -> str:
    """使用 bcrypt 生成密码哈希"""
    if len(password.encode("utf-8")) > 72:
        password = password[:72]  # bcrypt 的 72 字节限制
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码（bcrypt；历史明文/固定盐 SHA-256 仅用于存量账号登录）"""
    if not hashed_password:
        return False
    if is_bcrypt_hash(hashed_password):
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    # 历史弱哈希：仅用于校验存量账号，登录成功后会被重新哈希为 bcrypt
    return plain_password == hashed_password or _legacy_hash(plain_password) == hashed_password


def needs_rehash(hashed_password: str) -> bool:
    """是否为需要迁移到 bcrypt 的弱哈希"""
    return not is_bcrypt_hash(hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建 access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    """创建 refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


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
    """使用 refresh token 刷新 access token"""
    payload = verify_token(refresh_token, token_type="refresh")
    if payload is None:
        return None
    return create_access_token(data={"sub": payload.get("sub"), "role": payload.get("role")})


def authenticate_user(db: Session, username: str, password: str):
    """验证用户；若密码为历史弱哈希，验证通过后自动升级为 bcrypt"""
    from backend.database.users import get_user_by_session

    user = get_user_by_session(db, username)
    if not user:
        return None
    if not verify_password(password, user.password or ""):
        return None

    # 弱哈希/明文密码：登录成功后透明升级为 bcrypt
    if needs_rehash(user.password):
        user.password = get_password_hash(password)
        db.commit()

    return user.to_dict()
