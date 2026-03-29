"""AI機能API — ドキュメント生成・セマンティック検索・Q&A

設計意図: サービス層（ai_service / rag_service）を実体接続し、
プラン別制限・プロンプトインジェクション対策・エラーハンドリングを統合する。
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.ai_helpers import (
    check_generation_limit,
    fallback_db_search,
    get_workspace_document_ids,
    get_workspace_plan,
    hits_to_results,
)
from app.api.v1.workspaces import _verify_membership
from app.core.sanitize import filter_llm_output, sanitize_user_input, truncate_for_token_limit
from app.models.ai_log import AIGeneration, SearchLog
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
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces/{workspace_id}/ai", tags=["AI機能"])


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_document(
    workspace_id: uuid.UUID,
    body: AIGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIGeneration:
    """AIでドキュメントを自動生成 — LLM Gatewayを経由"""
    await _verify_membership(db, workspace_id, current_user.id)

    plan = await get_workspace_plan(db, workspace_id)
    await check_generation_limit(db, workspace_id, plan)

    # プロンプトインジェクション対策 + トークン上限対策
    safe_prompt = truncate_for_token_limit(sanitize_user_input(body.prompt))

    try:
        result = await ai_service.generate_document(safe_prompt, body.model)
    except RuntimeError as e:
        logger.error("LLM生成エラー: %s", e)
        raise HTTPException(status_code=503, detail="AI生成サービスが一時的に利用できません") from e
    except Exception as e:
        logger.error("LLM生成で予期しないエラー: %s", e)
        if "rate_limit" in str(e).lower() or "429" in str(e):
            raise HTTPException(
                status_code=429, detail="AIプロバイダーのレート制限に達しました。しばらくお待ちください。"
            ) from e
        raise HTTPException(status_code=502, detail="AI生成中にエラーが発生しました") from e

    log = AIGeneration(
        workspace_id=workspace_id,
        user_id=current_user.id,
        input_text=body.prompt,
        generated_content=filter_llm_output(result.content),
        model_used=result.model,
        tokens_used=result.total_tokens,
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
    """セマンティック検索 — Qdrant優先、障害時はDB全文検索にフォールバック"""
    await _verify_membership(db, workspace_id, current_user.id)

    safe_query = sanitize_user_input(body.query)
    doc_ids = await get_workspace_document_ids(db, workspace_id)
    results: list[AISearchResult] = []

    try:
        if doc_ids:
            search_hits = await rag_service.search(safe_query, doc_ids, body.top_k)
            results = await hits_to_results(db, search_hits)
    except Exception as e:
        logger.warning("Qdrant検索エラー、DB全文検索にフォールバック: %s", e)
        results = await fallback_db_search(db, workspace_id, safe_query, body.top_k)

    db.add(SearchLog(
        workspace_id=workspace_id, user_id=current_user.id,
        query=body.query, results_count=len(results),
    ))
    return AISearchResponse(query=body.query, results=results, results_count=len(results))


@router.post("/ask", response_model=AIAskResponse)
async def ask_question(
    workspace_id: uuid.UUID,
    body: AIAskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AIAskResponse:
    """Q&A — RAGパイプラインで検索→コンテキスト構築→LLM回答生成"""
    await _verify_membership(db, workspace_id, current_user.id)

    safe_question = sanitize_user_input(body.question)
    doc_ids = await get_workspace_document_ids(db, workspace_id)
    sources: list[AISearchResult] = []
    context_chunks: list[str] = []

    try:
        if doc_ids:
            search_hits = await rag_service.search(safe_question, doc_ids, top_k=5)
            context_chunks = [r.chunk_text for r in search_hits]
            sources = await hits_to_results(db, search_hits)
    except Exception as e:
        logger.warning("RAG検索エラー、フォールバック: %s", e)
        sources = await fallback_db_search(db, workspace_id, safe_question, 5)
        context_chunks = [s.content_snippet for s in sources]

    if context_chunks:
        try:
            answer = filter_llm_output(
                await ai_service.generate_answer(safe_question, context_chunks)
            )
        except Exception as e:
            logger.error("Q&A回答生成エラー: %s", e)
            answer = "申し訳ありません。回答の生成中にエラーが発生しました。しばらくしてからお試しください。"
    else:
        answer = "関連するドキュメントが見つかりませんでした。"

    return AIAskResponse(answer=answer, sources=sources)


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
