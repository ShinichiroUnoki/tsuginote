"""ダッシュボードAPI — 統計情報・最近のアクティビティ"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.workspaces import _verify_membership
from app.models.ai_log import AIGeneration, SearchLog
from app.models.checklist import Checklist
from app.models.document import Document
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.schemas.dashboard import DashboardStats, RecentActivity

router = APIRouter(
    prefix="/workspaces/{workspace_id}/dashboard", tags=["ダッシュボード"]
)


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    """ワークスペースの統計情報"""
    await _verify_membership(db, workspace_id, current_user.id)

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 各種カウントを並列で取得
    doc_count = await db.execute(
        select(func.count(Document.id)).where(
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
        )
    )
    cl_count = await db.execute(
        select(func.count(Checklist.id)).where(
            Checklist.workspace_id == workspace_id
        )
    )
    member_count = await db.execute(
        select(func.count(WorkspaceMember.id)).where(
            WorkspaceMember.workspace_id == workspace_id
        )
    )
    ai_count = await db.execute(
        select(func.count(AIGeneration.id)).where(
            AIGeneration.workspace_id == workspace_id,
            AIGeneration.created_at >= month_start,
        )
    )
    search_count = await db.execute(
        select(func.count(SearchLog.id)).where(
            SearchLog.workspace_id == workspace_id,
            SearchLog.searched_at >= month_start,
        )
    )

    return DashboardStats(
        total_documents=doc_count.scalar_one(),
        total_checklists=cl_count.scalar_one(),
        total_members=member_count.scalar_one(),
        ai_generations_this_month=ai_count.scalar_one(),
        searches_this_month=search_count.scalar_one(),
    )


@router.get("/recent", response_model=list[RecentActivity])
async def get_recent(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecentActivity]:
    """最近のアクティビティ — 直近10件"""
    await _verify_membership(db, workspace_id, current_user.id)

    activities: list[RecentActivity] = []

    # 最近作成/更新されたドキュメント
    doc_result = await db.execute(
        select(Document, User)
        .join(User, Document.author_id == User.id)
        .where(
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
        )
        .order_by(Document.updated_at.desc())
        .limit(5)
    )
    for doc, user in doc_result.all():
        activities.append(
            RecentActivity(
                type="document_updated",
                title=doc.title,
                user_name=user.name,
                timestamp=doc.updated_at,
                resource_id=doc.id,
            )
        )

    # 最近のAI生成
    ai_result = await db.execute(
        select(AIGeneration, User)
        .join(User, AIGeneration.user_id == User.id)
        .where(AIGeneration.workspace_id == workspace_id)
        .order_by(AIGeneration.created_at.desc())
        .limit(5)
    )
    for gen, user in ai_result.all():
        activities.append(
            RecentActivity(
                type="ai_generated",
                title=gen.input_text[:50],
                user_name=user.name,
                timestamp=gen.created_at,
                resource_id=gen.id,
            )
        )

    # タイムスタンプでソートして上位10件
    activities.sort(key=lambda a: a.timestamp, reverse=True)
    return activities[:10]
