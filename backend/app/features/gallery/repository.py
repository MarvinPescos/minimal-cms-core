from app.infrastructure.database import UserScopeRepository
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from .models import  Image, Album
import uuid

class ImageRepository(UserScopeRepository[Image]):
    """Repository pattern for Gallery"""

    def __init__(self, session):
        super().__init__(Image, session)

    # ============ Custom Methods ============

    # ============ Public Access Methods ============

    async def get_public_images(self, user_id: uuid.UUID, limit: int = 100, offset: int = 0):
        """Get all images from published albums (public access)"""
        result = await self.session.execute(
            select(Image)
            .join(Album, Image.album_id == Album.id)
            .where(
                and_(
                    Image.user_id == user_id,
                    Album.is_published
                )
            )
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_public_image_by_slug(self, user_id: uuid.UUID, slug: str):
        """Get a single image by slug if its album is published (public access)"""
        result = await self.session.execute(
            select(Image)
            .join(Album, Image.album_id == Album.id)
            .where(
                and_(
                    Image.user_id == user_id,
                    Image.slug == slug,
                    Album.is_published
                )
            )
        )
        return result.scalar_one_or_none()

class AlbumRepository(UserScopeRepository[Album]):
    """Repository pattern for Gallery"""

    def __init__(self, session):
        super().__init__(Album, session)

    # ============ Custom Methods ============

    async def get_all_album_with_images(self, user_id: uuid.UUID, limit: int = 100, offset: int = 0):
        """Get all album and egearly load images"""

        result = await self.session.execute(
            select(Album)
            .options(selectinload(Album.images))
            .where(
                and_(
                    Album.user_id == user_id
                )
            )
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_album_with_images(self, user_id: uuid.UUID, album_id: uuid.UUID):
        """Eagerly load images"""

        result = await self.session.execute(
            select(Album)
            .options(selectinload(Album.images))
            .where(
                and_(
                    Album.user_id == user_id,
                    Album.id == album_id
                )
            )
        )

        return result.scalar_one_or_none()

