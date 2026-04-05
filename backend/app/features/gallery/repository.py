from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database import PublishableMixin, TenantScopeRepository, BaseRepository
from app.infrastructure.database.exceptions import DatabaseError
from app.infrastructure.observability import log
from .models import Image, Album
import uuid


class AlbumRepository(PublishableMixin, TenantScopeRepository[Album]):
    """Repository pattern for Album - tenant scoped"""

    def __init__(self, session):
        super().__init__(Album, session)

    # ============ Custom Methods ============

    async def get_all_albums(
        self,
        tenant_id: uuid.UUID,
        is_published: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await self.get_many(
            tenant_id=tenant_id,
            is_published=is_published,
            limit=limit,
            offset=offset,
        )


class ImageRepository(BaseRepository[Image]):
    """Repository for Image - scoped via Album JOIN, never exposes unscoped queries"""

    def __init__(self, session):
        super().__init__(Image, session)

    # ============ Custom Methods ============

    def _apply_album_identifier(self, query, album_identifier: str):
        """Helper to filter by album UUID or slug."""
        try:
            album_id = uuid.UUID(album_identifier)
            return query.where(Album.id == album_id)
        except ValueError:
            return query.where(Album.slug == album_identifier)

    async def get_by_album(
        self,
        tenant_id: uuid.UUID,
        album_identifier: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Image]:
        """Authenticated tenant view — all images, optionally filtered by album."""
        try:
            query = (
                select(Image)
                .join(Album, Image.album_id == Album.id)
                .where(Album.tenant_id == tenant_id)
            )
            if album_identifier:
                query = self._apply_album_identifier(query, album_identifier)
            result = await self.session.execute(query.limit(limit).offset(offset))
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error("database.error", model="Image", operation="get_by_album", error=str(e))
            raise DatabaseError("Failed to fetch images", original_error=e)

    async def get_public_images(
        self,
        tenant_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Image]:
        """Public view — all images from published albums, no album filtering."""
        try:
            result = await self.session.execute(
                select(Image)
                .join(Album, Image.album_id == Album.id)
                .where(
                    Album.tenant_id == tenant_id,
                    Album.is_published.is_(True),
                )
                .limit(limit).offset(offset)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error("database.error", model="Image", operation="get_public_images", error=str(e))
            raise DatabaseError("Failed to fetch public images", original_error=e)

    async def get_scoped_by_id(
        self,
        tenant_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> Image | None:
        """Get a single image verifying it belongs to the tenant via Album JOIN."""
        try:
            result = await self.session.execute(
                select(Image)
                .join(Album, Image.album_id == Album.id)
                .where(
                    Album.tenant_id == tenant_id,
                    Image.id == image_id,
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error("database.error", model="Image", operation="get_scoped_by_id", error=str(e))
            raise DatabaseError("Failed to fetch image", original_error=e)

