"""AI機能API — ドキュメント生成・セマンティック検索・Q&A"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.workspaces import _verify_membership
from app.models.ai_log import AIGeneration, SearchLog
from app.models.document import Document
from app.models.user import User
from app.schemas.ai import (
    AIAskRequest,
    AIAskResponse,
    AIGenerateRequest,
    AIGenerateResponse,
    AISearchRequest,
    AISearchResponse,
    AISearchResult,
    AIUsageResponse,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/ai", tags=["AI機能"]
)


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_document(
    workspace_id: uuid.UUID,
    body: AIGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIGeneration:
    """AIでドキュメントを自動生成 — LLM Gatewayを経由"""
    await _verify_membership(db, workspace_id, current_user.id)

    # TODO: ai_serviceを呼び出してLLM経由で生成する
    # 現時点ではプレースホルダーとして固定レスポンスを返す
    generated_content = (
        f"[AI生成プレースホルダー] プロンプト: {body.prompt[:100]}..."
    )
    model_used = body.model or "gpt-4o"
    tokens_used = len(body.prompt) + len(generated_content)

    log = AIGeneration(
        workspace_id=workspace_id,
        user_id=current_user.id,
        input_text=body.prompt,
        generated_content=generated_content,
        model_used=model_used,
        tokens_used=tokens_used,
    )
    db.add(log)
    await db.flush()
    return log


@router.post("/search", response_model=AISearchResponse)
async def semantic_search(
    workspace_id: uuid.UUID,
    body: AISearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AISearchResponse:
    """セマンティック検索 — Qdrantでベクトル類似度検索"""
    await _verify_membership(db, workspace_id, current_user.id)

    # TODO: rag_serviceを呼び出してQdrant経由で検索する
    # 現時点ではDBの全文検索でフォールバック
    result = await db.execute(
        select(Document)
        .where(
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
            Document.title.ilike(f"%{body.query}%")
            | Document.content.ilike(f"%{body.query}%"),
        )
        .limit(body.top_k)
    )
    docs = result.scalars().all()

    results = [
        AISearchResult(
            document_id=doc.id,
            title=doc.title,
            content_snippet=(doc.content or "")[:200],
            score=1.0,  # プレースホルダー
        )
        for doc in docs
    ]

    # 検索ログ記録
    search_log = SearchLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        query=body.query,
        results_count=len(results),
    )
    db.add(search_log)

    return AISearchResponse(
        query=body.query,
        results=results,
        results_count=len(results),
    )


@router.post("/ask", response_model=AIAskResponse)
async def ask_question(
    workspace_id: uuid.UUID,
    body: AIAskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIAskResponse:
    """Q&A — RAGパイプラインで回答生成"""
    await _verify_membership(db, workspace_id, current_user.id)

    # TODO: RAGパイプラインを実装 — 検索 → コンテキスト構築 → LLM回答生成
    # 現時点ではプレースホルダー
    result = await db.execute(
        select(Document)
        .where(
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
        )
        .limit(5)
    )
    docs = result.scalars().all()
    sources = [
        AISearchResult(
            document_id=doc.id,
            title=doc.title,
            content_snippet=(doc.content or "")[:200],
            score=1.0,
        )
        for doc in docs
    ]

    return AIAskResponse(
        answer=f"[AI回答プレースホルダー] 質問: {body.question[:100]}",
        sources=sources,
    )


@router.get("/usage", response_model=AIUsageResponse)
async def get_usage(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIUsageResponse:
    """AI利用状況 — 今月の生成回数・検索回数・トークン使用量"""
    await _verify_membership(db, workspace_id, current_user.id)

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 今月の生成回数・トークン数
    gen_result = await db.execute(
        select(
            func.count(AIGeneration.id),
            func.coalesce(func.sum(AIGeneration.tokens_used), 0),
        ).where(
            AIGeneration.workspace_id == workspace_id,
            AIGeneration.created_at >= month_start,
        )
    )
    gen_count, total_tokens = gen_result.one()

    # 今月の検索回数
    search_result = await db.execute(
        select(func.count(SearchLog.id)).where(
            SearchLog.workspace_id == workspace_id,
            SearchLog.searched_at >= month_start,
        )
    )
    search_count = search_result.scalar_one()

    return AIUsageResponse(
        total_generations=gen_count,
        total_searches=search_count,
        total_tokens_used=total_tokens,
        period=now.strftime("%Y-%m"),
    )
