"""認証関連のPydanticスキーマ — リクエスト/レスポンスの型定義"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """サインアップリクエスト"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """パスワード複雑性チェック — ブルートフォース耐性の確保"""
        if not re.search(r"[A-Z]", v):
            raise ValueError("パスワードには大文字を1文字以上含めてください")
        if not re.search(r"[a-z]", v):
            raise ValueError("パスワードには小文字を1文字以上含めてください")
        if not re.search(r"\d", v):
            raise ValueError("パスワードには数字を1文字以上含めてください")
        return v


class UserLogin(BaseModel):
    """ログインリクエスト"""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """プロフィール更新リクエスト — 変更したいフィールドのみ送信"""

    name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""

    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT トークンペアのレスポンス"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """トークン更新リクエスト"""

    refresh_token: str
