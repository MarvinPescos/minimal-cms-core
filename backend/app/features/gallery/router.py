from fastapi import APIRouter, Depends, status, UploadFile, File
from typing import List
import uuid

from app.infrastructure.security import require_auth, AuthenticatedUser
from .schemas import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    ImageResponse
)
from .service import AlbumService, ImageService
from .dependencies import get_album_service, get_image_service

router = APIRouter(prefix="/gallery", tags=["Gallery"])


# ============================================================
# Public Endpoints (no auth required - for landing pages)
# ============================================================

@router.get(
    "/public/images",
    response_model=List[ImageResponse],
    summary="List all public images for a tenant"
)
async def list_public_images(
    user_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
    service: ImageService = Depends(get_image_service)
):
    """
    Get all images from published albums for a tenant's landing page.
    
    - **user_id**: The tenant's UUID (required)
    - **limit**: Maximum images to return (default: 100)
    - **offset**: Pagination offset (default: 0)
    
    Note: Only images from published albums are returned.
    """
    return await service.get_public_images(user_id, limit, offset)


@router.get(
    "/public/images/{slug}",
    response_model=ImageResponse,
    summary="Get a public image by slug"
)
async def get_public_image(
    slug: str,
    user_id: uuid.UUID,
    service: ImageService = Depends(get_image_service)
):
    """
    Get a single image by its slug (SEO-friendly).
    
    - **slug**: The image's URL-friendly slug
    - **user_id**: The tenant's UUID (required)
    
    Note: Only images from published albums are accessible.
    """
    return await service.get_public_image_by_slug(user_id, slug)


# ============================================================
# Album Endpoints (auth required - admin only)
# ============================================================

@router.post(
    "/albums",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new album"
)
async def create_album(
    data: AlbumCreate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Create a new album for the authenticated user.
    
    - **title**: Album title (3-150 characters)
    - **is_published**: Whether album is publicly visible (default: false)
    
    Cover image is auto-set when the first image is uploaded to the album.
    """
    return await service.create_album(
        user_id=uuid.UUID(current_user.user_id),
        data=data
    )


@router.get(
    "/albums",
    response_model=List[AlbumResponse],
    summary="Get all albums for current user"
)
async def get_albums(
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Retrieve all albums belonging to the authenticated user.
    """
    return await service.get_user_albums(
        user_id=uuid.UUID(current_user.user_id)
    )


@router.get(
    "/albums/{album_id}",
    response_model=AlbumResponse,
    summary="Get a single album with its images"
)
async def get_album(
    album_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Retrieve a specific album by ID, including all its images.
    """
    return await service.get_album(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id
    )


@router.patch(
    "/albums/{album_id}",
    response_model=AlbumResponse,
    summary="Update an album"
)
async def update_album(
    album_id: uuid.UUID,
    data: AlbumUpdate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Partially update an existing album.
    
    - **title**: New album title (optional)
    - **is_published**: Update publish status (optional)
    """
    return await service.update_album(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id,
        data=data
    )


@router.delete(
    "/albums/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an album"
)
async def delete_album(
    album_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Permanently delete an album and all its images.
    
    **Warning**: This action cannot be undone. All images in the album will be deleted.
    """
    await service.delete_album(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id
    )


# ============================================================
# Image Endpoints (within Albums)
# ============================================================

@router.post(
    "/albums/{album_id}/images",
    response_model=List[ImageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload images to an album"
)
async def upload_images(
    album_id: uuid.UUID,
    files: List[UploadFile] = File(..., description="Image files to upload (max 5MB each)"),
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """
    Bulk upload images to a specific album.
    
    - Supported formats: JPEG, PNG, WebP
    - Maximum file size: 5MB per image
    - Slugs are auto-generated from album title
    - First uploaded image becomes album cover (if no cover exists)
    """
    return await service.upload_images(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id,
        files=files
    )


@router.get(
    "/images",
    response_model=List[ImageResponse],
    summary="Get all images for current user"
)
async def get_user_images(
    limit: int = 100,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """
    Retrieve all images belonging to the authenticated user (across all albums).
    
    - **limit**: Maximum number of images to return (default: 100)
    - **offset**: Number of images to skip for pagination (default: 0)
    """
    return await service.get_user_images(
        user_id=uuid.UUID(current_user.user_id),
        limit=limit,
        offset=offset
    )


@router.get(
    "/images/{slug}",
    response_model=ImageResponse,
    summary="Get a single image by slug"
)
async def get_image_by_slug(
    slug: str,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """
    Retrieve a specific image by its unique slug.
    
    The slug can be used as alt text for SEO purposes.
    """
    return await service.get_image_by_slug(
        user_id=uuid.UUID(current_user.user_id),
        slug=slug
    )