"""チェックリストモデル — 引き継ぎ用タスクリストの管理"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Checklist(Base):
    __tablename__ = "checklists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    title: Mapped[str] = mapped_column(String(500))
    # テンプレートタイプ: custom / onboarding / offboarding / project
    template_type: Mapped[str] = mapped_column(String(50), default="custom")
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )

    # リレーション
    workspace: Mapped["Workspace"] = relationship(back_populates="checklists")  # noqa: F821
    creator: Mapped["User"] = relationship()  # noqa: F821
    items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="checklist", lazy="selectin", cascade="all, delete-orphan"
    )


class ChecklistItem(Base):
    """チェックリストの個別アイテム — ドキュメントへのリンクも可能"""

    __tablename__ = "checklist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    checklist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checklists.id"), index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(1000))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    checklist: Mapped["Checklist"] = relationship(back_populates="items")
    document: Mapped["Document | None"] = relationship()  # noqa: F821
