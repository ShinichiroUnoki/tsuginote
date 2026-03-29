"""ダッシュボード関連のPydanticスキーマ"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """ワークスペース統計情報"""

    total_documents: int
    total_checklists: int
    total_members: int
    ai_generations_this_month: int
    searches_this_month: int


class RecentActivity(BaseModel):
    """最近のアクティビティ"""

    type: str  # document_created / document_updated / checklist_created / ai_generated
    title: str
    user_name: str
    timestamp: datetime
    resource_id: uuid.UUID


class DashboardResponse(BaseModel):
    """ダッシュボードレスポンス"""

    stats: DashboardStats
    recent: list[RecentActivity]
