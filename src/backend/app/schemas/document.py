"""ドキュメント関連のPydanticスキーマ"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """ドキュメント作成リクエスト"""

    title: str = Field(min_length=1, max_length=500)
    content: str | None = None
    category: str | None = Field(None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    is_ai_generated: bool = False


class DocumentUpdate(BaseModel):
    """ドキュメント更新リクエスト"""

    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = None
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None


class DocumentResponse(BaseModel):
    """ドキュメント情報レスポンス"""

    id: uuid.UUID
    workspace_id: uuid.UUID
    author_id: uuid.UUID
    title: str
    content: str | None
    category: str | None
    is_ai_generated: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """ドキュメント一覧レスポンス — contentを省略して軽量化"""

    id: uuid.UUID
    workspace_id: uuid.UUID
    author_id: uuid.UUID
    title: str
    category: str | None
    is_ai_generated: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentVersionResponse(BaseModel):
    """バージョン履歴レスポンス"""

    id: uuid.UUID
    document_id: uuid.UUID
    editor_id: uuid.UUID
    version_number: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
