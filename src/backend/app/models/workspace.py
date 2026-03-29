"""ワークスペース・メンバーモデル — チーム単位のデータ分離の基盤"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # プラン: free / pro / enterprise
    plan: Mapped[str] = mapped_column(String(50), default="free")
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )

    # リレーション
    owner: Mapped["User"] = relationship(back_populates="owned_workspaces")  # noqa: F821
    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace", lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="workspace", lazy="selectin"
    )
    checklists: Mapped[list["Checklist"]] = relationship(  # noqa: F821
        back_populates="workspace", lazy="selectin"
    )


class WorkspaceMember(Base):
    """ワークスペースへの参加情報 — role で権限レベルを管理"""

    __tablename__ = "workspace_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    # role: owner / admin / member / viewer
    role: Mapped[str] = mapped_column(String(50), default="member")
    joined_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )

    # リレーション
    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")  # noqa: F821
