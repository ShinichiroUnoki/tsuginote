"""ワークスペースAPI — 作成・一覧・詳細・更新・メンバー管理"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import (
    InviteRequest,
    MemberResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["ワークスペース"])


async def _verify_membership(
    db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> WorkspaceMember:
    """ユーザーがワークスペースのメンバーか検証 — アクセス制御の基盤"""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このワークスペースへのアクセス権がありません",
        )
    return member


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """ワークスペース作成 — 作成者は自動的にownerメンバーになる"""
    workspace = Workspace(
        name=body.name,
        description=body.description,
        owner_id=current_user.id,
    )
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(member)
    return workspace


@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Workspace]:
    """自分が所属するワークスペース一覧"""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """ワークスペース詳細取得"""
    await _verify_membership(db, workspace_id, current_user.id)
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="ワークスペースが見つかりません")
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    body: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """ワークスペース更新 — owner/adminのみ"""
    member = await _verify_membership(db, workspace_id, current_user.id)
    if member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="更新権限がありません")

    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="ワークスペースが見つかりません")

    if body.name is not None:
        workspace.name = body.name
    if body.description is not None:
        workspace.description = body.description
    db.add(workspace)
    return workspace


@router.post("/{workspace_id}/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    workspace_id: uuid.UUID,
    body: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """メンバー招待 — owner/adminのみ。既存ユーザーのメールで招待"""
    member = await _verify_membership(db, workspace_id, current_user.id)
    if member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="招待権限がありません")

    # 招待対象のユーザーを検索
    result = await db.execute(select(User).where(User.email == body.email))
    target_user = result.scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 既にメンバーか確認
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="既にメンバーです")

    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=target_user.id,
        role=body.role,
    )
    db.add(new_member)
    return {"message": "メンバーを招待しました"}


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberResponse]:
    """ワークスペースメンバー一覧"""
    await _verify_membership(db, workspace_id, current_user.id)
    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    rows = result.all()
    return [
        MemberResponse(
            id=m.id,
            user_id=m.user_id,
            role=m.role,
            joined_at=m.joined_at,
            user_name=u.name,
            user_email=u.email,
        )
        for m, u in rows
    ]


@router.delete(
    "/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """メンバー削除 — owner/adminのみ。ownerは削除不可"""
    caller = await _verify_membership(db, workspace_id, current_user.id)
    if caller.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="削除権限がありません")

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")
    if target.role == "owner":
        raise HTTPException(status_code=400, detail="オーナーは削除できません")

    await db.delete(target)
