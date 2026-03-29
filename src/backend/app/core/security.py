"""JWT生成・検証とパスワードハッシュ — 認証の中核モジュール"""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt cost factor 12 — セキュリティ設計書の指定値
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """平文パスワードをbcryptハッシュに変換"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュを照合"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # 不正なハッシュ形式の場合もFalseを返す（タイミング攻撃対策のダミーハッシュ等）
        return False


def create_access_token(subject: str) -> str:
    """アクセストークン生成 — 有効期限30分、iat/jtiクレーム付き"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    """リフレッシュトークン生成 — 有効期限7日、iat/jtiクレーム付き"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """JWTをデコードし、ペイロードを返す。無効なら None"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
