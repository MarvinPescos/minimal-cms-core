from sqlalchemy import Boolean, String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING
import uuid, enum


from app.infrastructure.database import Base, TimestampMixin
from app.features.users.models import User

if (TYPE_CHECKING):
    from app.features.gallery.models import Album


class TenantRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    albums: Mapped[list["Album"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    members: Mapped[list["TenantMembers"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan"
    )

class TenantMembers(Base, TimestampMixin):
    __tablename__ = "tenant_members"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=TenantRole.MEMBER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="memberships", lazy="selectin")
    tenant: Mapped["Tenant"] = relationship(back_populates="members", lazy="selectin")

    __table_args__ = (
        Index("ix_tenant_members_user_tenant", "user_id", "tenant_id", unique=True),
    )
