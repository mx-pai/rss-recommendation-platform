from datetime import datetime, timezone, timedelta
from typing import Optional
from jose import JWSError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hash_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hash_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: Optional[str] = payload.get("sub")
        if username is None:
            return None
        return username
    except JWSError:
        return None


