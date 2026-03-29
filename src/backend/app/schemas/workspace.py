"""ワークスペース関連のPydanticスキーマ"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    """ワークスペース作成リクエスト"""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class WorkspaceUpdate(BaseModel):
    """ワークスペース更新リクエスト"""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class WorkspaceResponse(BaseModel):
    """ワークスペース情報レスポンス"""

    id: uuid.UUID
    name: str
    description: str | None
    plan: str
    owner_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    """ワークスペースメンバー情報"""

    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    user_name: str
    user_email: str


class InviteRequest(BaseModel):
    """メンバー招待リクエスト"""

    email: str
    role: str = Field(default="member", pattern="^(admin|member|viewer)$")
