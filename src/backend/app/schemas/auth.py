"""認証関連のPydanticスキーマ — リクエスト/レスポンスの型定義"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """サインアップリクエスト"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


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
