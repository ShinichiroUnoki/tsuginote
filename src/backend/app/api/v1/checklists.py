"""チェックリストAPI — CRUD + アイテム更新"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.workspaces import _verify_membership
from app.models.checklist import Checklist, ChecklistItem
from app.models.user import User
from app.schemas.checklist import (
    ChecklistCreate,
    ChecklistItemUpdate,
    ChecklistListResponse,
    ChecklistResponse,
    ChecklistUpdate,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/checklists", tags=["チェックリスト"]
)


@router.post("/", response_model=ChecklistResponse, status_code=status.HTTP_201_CREATED)
async def create_checklist(
    workspace_id: uuid.UUID,
    body: ChecklistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChecklistResponse:
    """チェックリスト作成 — アイテムも同時に登録"""
    await _verify_membership(db, workspace_id, current_user.id)

    checklist = Checklist(
        workspace_id=workspace_id,
        creator_id=current_user.id,
        title=body.title,
        template_type=body.template_type,
    )
    db.add(checklist)
    await db.flush()

    for item in body.items:
        db.add(
            ChecklistItem(
                checklist_id=checklist.id,
                description=item.description,
                document_id=item.document_id,
                sort_order=item.sort_order,
            )
        )

    await db.flush()
    await db.refresh(checklist)

    return ChecklistResponse(
        id=checklist.id,
        workspace_id=checklist.workspace_id,
        creator_id=checklist.creator_id,
        title=checklist.title,
        template_type=checklist.template_type,
        items=[
            _item_to_response(i) for i in checklist.items
        ],
        created_at=checklist.created_at,
    )


def _item_to_response(item: ChecklistItem) -> dict:
    return {
        "id": item.id,
        "checklist_id": item.checklist_id,
        "document_id": item.document_id,
        "description": item.description,
        "is_completed": item.is_completed,
        "sort_order": item.sort_order,
    }


@router.get("/", response_model=list[ChecklistListResponse])
async def list_checklists(
    workspace_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChecklistListResponse]:
    """チェックリスト一覧 — 完了数付き"""
    await _verify_membership(db, workspace_id, current_user.id)

    result = await db.execute(
        select(Checklist)
        .where(Checklist.workspace_id == workspace_id)
        .order_by(Checklist.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    checklists = result.scalars().unique().all()

    return [
        ChecklistListResponse(
            id=cl.id,
            workspace_id=cl.workspace_id,
            creator_id=cl.creator_id,
            title=cl.title,
            template_type=cl.template_type,
            items_count=len(cl.items),
            completed_count=sum(1 for i in cl.items if i.is_completed),
            created_at=cl.created_at,
        )
        for cl in checklists
    ]


@router.get("/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(
    workspace_id: uuid.UUID,
    checklist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChecklistResponse:
    """チェックリスト詳細取得"""
    await _verify_membership(db, workspace_id, current_user.id)

    result = await db.execute(
        select(Checklist).where(
            Checklist.id == checklist_id,
            Checklist.workspace_id == workspace_id,
        )
    )
    checklist = result.scalar_one_or_none()
    if checklist is None:
        raise HTTPException(status_code=404, detail="チェックリストが見つかりません")

    return ChecklistResponse(
        id=checklist.id,
        workspace_id=checklist.workspace_id,
        creator_id=checklist.creator_id,
        title=checklist.title,
        template_type=checklist.template_type,
        items=[_item_to_response(i) for i in checklist.items],
        created_at=checklist.created_at,
    )


@router.put("/{checklist_id}", response_model=ChecklistResponse)
async def update_checklist(
    workspace_id: uuid.UUID,
    checklist_id: uuid.UUID,
    body: ChecklistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChecklistResponse:
    """チェックリストのタイトル更新"""
    await _verify_membership(db, workspace_id, current_user.id)

    result = await db.execute(
        select(Checklist).where(
            Checklist.id == checklist_id,
            Checklist.workspace_id == workspace_id,
        )
    )
    checklist = result.scalar_one_or_none()
    if checklist is None:
        raise HTTPException(status_code=404, detail="チェックリストが見つかりません")

    if body.title is not None:
        checklist.title = body.title
    db.add(checklist)
    await db.flush()
    await db.refresh(checklist)

    return ChecklistResponse(
        id=checklist.id,
        workspace_id=checklist.workspace_id,
        creator_id=checklist.creator_id,
        title=checklist.title,
        template_type=checklist.template_type,
        items=[_item_to_response(i) for i in checklist.items],
        created_at=checklist.created_at,
    )


@router.put("/{checklist_id}/items/{item_id}")
async def update_checklist_item(
    workspace_id: uuid.UUID,
    checklist_id: uuid.UUID,
    item_id: uuid.UUID,
    body: ChecklistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """チェックリストアイテム更新 — 完了状態の切り替え等"""
    await _verify_membership(db, workspace_id, current_user.id)

    result = await db.execute(
        select(ChecklistItem)
        .join(Checklist)
        .where(
            ChecklistItem.id == item_id,
            ChecklistItem.checklist_id == checklist_id,
            Checklist.workspace_id == workspace_id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="アイテムが見つかりません")

    if body.description is not None:
        item.description = body.description
    if body.is_completed is not None:
        item.is_completed = body.is_completed
    if body.sort_order is not None:
        item.sort_order = body.sort_order
    if body.document_id is not None:
        item.document_id = body.document_id

    db.add(item)
    return _item_to_response(item)
