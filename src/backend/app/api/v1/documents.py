"""ドキュメントAPI — CRUD + バージョン履歴 + RAGインデックス自動更新"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.workspaces import _verify_membership
from app.models.document import Document, DocumentTag, DocumentVersion
from app.models.user import User
from app.services.rag_service import rag_service
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentVersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/documents", tags=["ドキュメント"]
)


async def _index_document_async(document_id: uuid.UUID, content: str) -> None:
    """RAGインデックスを非同期更新 — Qdrant障害時はログのみで継続"""
    try:
        await rag_service.index_document(document_id, content)
    except Exception as e:
        logger.warning("RAGインデックス更新失敗（ドキュメント %s）: %s", document_id, e)


async def _delete_document_index(document_id: uuid.UUID) -> None:
    """RAGインデックスからドキュメントを削除 — Qdrant障害時はログのみ"""
    try:
        await rag_service.delete_document(document_id)
    except Exception as e:
        logger.warning("RAGインデックス削除失敗（ドキュメント %s）: %s", document_id, e)


def _to_document_response(doc: Document) -> DocumentResponse:
    """ORMオブジェクトからレスポンス形式に変換"""
    return DocumentResponse(
        id=doc.id,
        workspace_id=doc.workspace_id,
        author_id=doc.author_id,
        title=doc.title,
        content=doc.content,
        category=doc.category,
        is_ai_generated=doc.is_ai_generated,
        tags=[t.tag_name for t in doc.tags],
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _to_document_list_response(doc: Document) -> DocumentListResponse:
    return DocumentListResponse(
        id=doc.id,
        workspace_id=doc.workspace_id,
        author_id=doc.author_id,
        title=doc.title,
        category=doc.category,
        is_ai_generated=doc.is_ai_generated,
        tags=[t.tag_name for t in doc.tags],
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    workspace_id: uuid.UUID,
    body: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """ドキュメント作成 — タグも同時に登録"""
    await _verify_membership(db, workspace_id, current_user.id)

    doc = Document(
        workspace_id=workspace_id,
        author_id=current_user.id,
        title=body.title,
        content=body.content,
        category=body.category,
        is_ai_generated=body.is_ai_generated,
    )
    db.add(doc)
    await db.flush()

    for tag_name in body.tags:
        db.add(DocumentTag(document_id=doc.id, tag_name=tag_name))

    # 初期バージョンを保存
    if body.content:
        db.add(
            DocumentVersion(
                document_id=doc.id,
                editor_id=current_user.id,
                content=body.content,
                version_number=1,
            )
        )

    await db.flush()
    await db.refresh(doc)

    # RAGインデックスに登録（ドキュメント内容がある場合）
    if body.content:
        await _index_document_async(doc.id, body.content)

    return _to_document_response(doc)


@router.get("/", response_model=list[DocumentListResponse])
async def list_documents(
    workspace_id: uuid.UUID,
    category: str | None = Query(None),
    tag: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentListResponse]:
    """ドキュメント一覧 — カテゴリ・タグでフィルタ可能"""
    await _verify_membership(db, workspace_id, current_user.id)

    query = select(Document).where(
        Document.workspace_id == workspace_id,
        Document.is_deleted == False,  # noqa: E712
    )

    if category:
        query = query.where(Document.category == category)
    if tag:
        query = query.join(DocumentTag).where(DocumentTag.tag_name == tag)

    query = query.order_by(Document.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    docs = result.scalars().unique().all()
    return [_to_document_list_response(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """ドキュメント詳細取得"""
    await _verify_membership(db, workspace_id, current_user.id)

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")
    return _to_document_response(doc)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    body: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """ドキュメント更新 — 変更時にバージョン履歴を自動保存"""
    await _verify_membership(db, workspace_id, current_user.id)

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    if body.title is not None:
        doc.title = body.title
    if body.category is not None:
        doc.category = body.category

    # content変更時にバージョン履歴を作成
    if body.content is not None and body.content != doc.content:
        # 現在の最新バージョン番号を取得
        ver_result = await db.execute(
            select(DocumentVersion.version_number)
            .where(DocumentVersion.document_id == doc.id)
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )
        latest_ver = ver_result.scalar_one_or_none() or 0

        db.add(
            DocumentVersion(
                document_id=doc.id,
                editor_id=current_user.id,
                content=body.content,
                version_number=latest_ver + 1,
            )
        )
        doc.content = body.content

    # タグの差し替え
    if body.tags is not None:
        # 既存タグを削除して新しいタグを追加
        for tag in doc.tags:
            await db.delete(tag)
        await db.flush()
        for tag_name in body.tags:
            db.add(DocumentTag(document_id=doc.id, tag_name=tag_name))

    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    # content変更時にRAGインデックスを再構築
    if body.content is not None:
        await _index_document_async(doc.id, doc.content or "")

    return _to_document_response(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """ドキュメント削除（ソフトデリート）"""
    await _verify_membership(db, workspace_id, current_user.id)

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
            Document.is_deleted == False,  # noqa: E712
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    doc.is_deleted = True
    db.add(doc)

    # RAGインデックスからも削除
    await _delete_document_index(doc.id)


@router.get(
    "/{document_id}/versions", response_model=list[DocumentVersionResponse]
)
async def list_versions(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentVersion]:
    """ドキュメントの変更履歴一覧"""
    await _verify_membership(db, workspace_id, current_user.id)

    # ドキュメント存在確認
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )
    )
    if doc_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")

    result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
    )
    return list(result.scalars().all())
