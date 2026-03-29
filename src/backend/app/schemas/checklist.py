"""チェックリスト関連のPydanticスキーマ"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChecklistItemCreate(BaseModel):
    """チェックリストアイテム"""

    description: str = Field(min_length=1, max_length=1000)
    document_id: uuid.UUID | None = None
    sort_order: int = 0


class ChecklistCreate(BaseModel):
    """チェックリスト作成リクエスト"""

    title: str = Field(min_length=1, max_length=500)
    template_type: str = Field(default="custom", max_length=50)
    items: list[ChecklistItemCreate] = Field(default_factory=list)


class ChecklistUpdate(BaseModel):
    """チェックリスト更新リクエスト"""

    title: str | None = Field(None, min_length=1, max_length=500)


class ChecklistItemUpdate(BaseModel):
    """チェックリストアイテム更新リクエスト"""

    description: str | None = Field(None, min_length=1, max_length=1000)
    is_completed: bool | None = None
    sort_order: int | None = None
    document_id: uuid.UUID | None = None


class ChecklistItemResponse(BaseModel):
    """チェックリストアイテムレスポンス"""

    id: uuid.UUID
    checklist_id: uuid.UUID
    document_id: uuid.UUID | None
    description: str
    is_completed: bool
    sort_order: int

    model_config = {"from_attributes": True}


class ChecklistResponse(BaseModel):
    """チェックリストレスポンス"""

    id: uuid.UUID
    workspace_id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    template_type: str
    items: list[ChecklistItemResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChecklistListResponse(BaseModel):
    """チェックリスト一覧レスポンス — アイテム数のみ"""

    id: uuid.UUID
    workspace_id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    template_type: str
    items_count: int
    completed_count: int
    created_at: datetime
