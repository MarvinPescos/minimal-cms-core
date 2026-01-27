from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from .service import AlbumService, ImageService


def get_album_service(db: AsyncSession = Depends(get_db)) -> AlbumService:
    """Dependency injection for AlbumService"""
    return AlbumService(db)


def get_image_service(db: AsyncSession = Depends(get_db)) -> ImageService:
    """Dependency injection for ImageService"""
    return ImageService(db)