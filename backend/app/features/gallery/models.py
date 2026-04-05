from sqlalchemy import Boolean, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import List
import uuid

from app.infrastructure.database import Base, TimestampMixin
from app.features.tenants.models import Tenant


class Album(Base, TimestampMixin):
    __tablename__ = "album"

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
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_album_tenant_slug"),
    )

    # relationship
    tenant: Mapped["Tenant"] = relationship(back_populates="albums")
    images: Mapped[List["Image"]] = relationship(back_populates="album", cascade="all, delete-orphan")

class Image(Base, TimestampMixin):

    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("album.id", ondelete="CASCADE"),
        nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("album_id", "slug", name="uq_image_album_slug"),
    )

    #=== relationships ===
    album: Mapped["Album"] = relationship(back_populates="images")

    
    


