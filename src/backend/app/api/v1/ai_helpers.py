"""AI APIヘルパー — プラン制限・検索変換・フォールバック

設計意図: ai.pyのルートハンドラを200行以内に保つため、
共通ロジック（制限チェック・検索結果変換・DB全文検索フォールバック）を分離。
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_log import AIGeneration
from app.models.document import Document
from app.models.workspace import Workspace
from app.schemas.ai import AISearchResult
from app.services.rag_service import SearchResult

# プラン別のAI生成回数上限（月間）
PLAN_GENERATION_LIMITS: dict[str, int] = {
    "free": 30,
    "pro": 300,
    "enterprise": 1000,
}


async def check_generation_limit(
    db: AsyncSession, workspace_id: uuid.UUID, plan: str
) -> None:
    """プラン別の月間生成回数制限をチェック"""
    limit = PLAN_GENERATION_LIMITS.get(plan, 30)
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.count(AIGeneration.id)).where(
            AIGeneration.workspace_id == workspace_id,
            AIGeneration.created_at >= month_start,
        )
    )
    if result.scalar_one() >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"月間AI生成回数の上限（{limit}回）に達しました。プランのアップグレードをご検討ください。",
        )


async def get_workspace_plan(db: AsyncSession, workspace_id: uuid.UUID) -> str:
    """ワークスペースのプランを取得"""
    result = await db.execute(
        select(Workspace.plan).where(Workspace.id == workspace_id)
    )
    return result.scalar_one_or_none() or "free"


async def get_workspace_document_ids(
    db: AsyncSession, workspace_id: uuid.UUID
) -> list[uuid.UUID]:
    """ワークスペース内の有効なドキュメントIDを取得"""
    result = await db.execute(
        select(Document.id).where(
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def hits_to_results(
    db: AsyncSession, search_hits: list[SearchResult],
) -> list[AISearchResult]:
    """RAG検索結果をAPI応答形式に変換 — ドキュメントタイトルをDB取得"""
    found_ids = [r.document_id for r in search_hits]
    if not found_ids:
        return []
    doc_result = await db.execute(select(Document).where(Document.id.in_(found_ids)))
    doc_map = {d.id: d for d in doc_result.scalars().all()}
    return [
        AISearchResult(
            document_id=r.document_id,
            title=doc_map[r.document_id].title if r.document_id in doc_map else "",
            content_snippet=r.chunk_text[:200],
            score=r.score,
        )
        for r in search_hits
    ]


async def fallback_db_search(
    db: AsyncSession, workspace_id: uuid.UUID, query: str, top_k: int
) -> list[AISearchResult]:
    """Qdrant障害時のフォールバック — PostgreSQL ILIKE全文検索"""
    sanitized = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{sanitized}%"
    result = await db.execute(
        select(Document)
        .where(
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
            Document.title.ilike(pattern, escape="\\")
            | Document.content.ilike(pattern, escape="\\"),
        )
        .limit(top_k)
    )
    return [
        AISearchResult(
            document_id=doc.id, title=doc.title,
            content_snippet=(doc.content or "")[:200], score=0.5,
        )
        for doc in result.scalars().all()
    ]
