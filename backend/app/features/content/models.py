from sqlalchemy import String, JSON, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from typing import Any
import uuid

from app.infrastructure.database import Base, TimestampMixin, SoftDeleteMixin
from app.features.tenants.models import Tenant
from app.features.users.models import User


class ContentType(Base, TimestampMixin):
    __tablename__ = "content_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    label: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    json_schema :  Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped["Tenant"] = relationship(lazy="selectin")
    entries: Mapped[list["ContentEntry"]] = relationship(
        back_populates="content_type", 
        cascade="all, delete-orphan"
    )

    __table_args__ = (Index(
        "ix_content_types_tenant_names", "tenant_id", "name", unique=True
    ),)

class ContentEntry(Base, TimestampMixin):
    __tablename__ = "content_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )
    content_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_types.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    cover_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(default=0)

    tenant: Mapped["Tenant"] = relationship(lazy="selectin")
    content_type: Mapped["ContentType"] = relationship(back_populates="entries", lazy="selectin")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by], lazy="selectin")
    editor: Mapped["User"] = relationship(foreign_keys=[updated_by], lazy="selectin")

    __table_args__ = (
        Index("ix_content_entries_tenant_slug", "tenant_id", "slug", unique=True),
        Index("ix_content_entries_tenant_type", "tenant_id", "content_type_id")
    )







