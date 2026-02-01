from fastapi import APIRouter, Depends, status, Request, UploadFile, File
from typing import List
import uuid

from app.infrastructure.security import require_auth, AuthenticatedUser
from app.infrastructure.cache import limiter, RateLimits
from .schemas import (
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    ImageResponse
)
from .service import AlbumService, ImageService
from .dependencies import get_album_service, get_image_service

router_album = APIRouter(prefix="/album", tags=["Album"])
router_image = APIRouter(prefix="/image", tags=["Image"])


# ============================================================
# Public Endpoints (no auth required - for landing pages)
# ============================================================

@router_image.get(
    "/public",
    response_model=List[ImageResponse],
    status_code=status.HTTP_200_OK,
    summary="List all public images",
    description="""
    Retrieve all images from published albums for a tenant's landing page.
    
    - **No Authentication Required**: This is a public endpoint.
    - **Filtering**: Only images from published albums are returned.
    - **Pagination**: Use limit and offset for pagination.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "List of public images retrieved successfully"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def list_public_images(
    request: Request,
    user_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
    service: ImageService = Depends(get_image_service)
):
    """Get all images from published albums for a tenant's landing page."""
    return await service.get_public_images(user_id, limit, offset)


@router_image.get(
    "/public/{slug}",
    response_model=ImageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public image by slug",
    description="""
    Retrieve a single image by its SEO-friendly slug.
    
    - **No Authentication Required**: This is a public endpoint.
    - **SEO-Friendly**: Uses slug instead of UUID for cleaner URLs.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "Image details retrieved successfully"},
        404: {"description": "Image not found or album not published"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_public_image(
    request: Request,
    slug: str,
    user_id: uuid.UUID,
    service: ImageService = Depends(get_image_service)
):
    """Get a single image by its slug (SEO-friendly)."""
    return await service.get_public_image_by_slug(user_id, slug)


@router_album.get(
    "/public/{slug}",
    response_model=AlbumResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public album by slug",
    description="""
    Retrieve a single album by its SEO-friendly slug.
    
    - **No Authentication Required**: This is a public endpoint.
    - **SEO-Friendly**: Uses slug instead of UUID for cleaner URLs.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "Album details retrieved successfully"},
        404: {"description": "Album not found or album not published"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_public_album(
    request: Request,
    slug: str,
    user_id: uuid.UUID,
    service: AlbumService = Depends(get_album_service)
):
    """Get a single album by its slug (SEO-friendly)."""
    return await service.get_public_album_by_slug(user_id, slug)


@router_album.get(
    "/public",
    response_model=List[AlbumResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all public album",
    description="""
    Retrieve all album from published albums for a tenant's landing page.
    
    - **No Authentication Required**: This is a public endpoint.
    - **SEO-Friendly**: Uses slug instead of UUID for cleaner URLs.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "Album details retrieved successfully"},
        404: {"description": "Album not found or album not published"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_all_public_albums(
    request: Request,
    user_id: uuid.UUID,
    service: AlbumService = Depends(get_album_service)
):
    """Get all published albums for a tenant's landing page."""
    return await service.get_all_public_album(user_id)


# ============================================================
# Album Endpoints (auth required - admin only)
# ============================================================

@router_album.post(
    "/",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new album",
    description="""
    Create a new album for the authenticated user.
    
    - **Title**: Album title (3-150 characters).
    - **Draft Mode**: Set is_published to false to save as draft.
    - **Cover Image**: Auto-set when the first image is uploaded.
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        201: {"description": "Album created successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "User is not authenticated"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def create_album(
    request: Request,
    data: AlbumCreate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """Create a new album for the authenticated user."""
    return await service.create_album(
        user_id=uuid.UUID(current_user.user_id),
        data=data
    )


@router_album.get(
    "/",
    response_model=List[AlbumResponse],
    status_code=status.HTTP_200_OK,
    summary="List all albums",
    description="""
    Retrieve all albums belonging to the authenticated user.
    
    - **Authorization**: User can only access their own albums.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "List of albums retrieved successfully"},
        401: {"description": "User is not authenticated"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_albums(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """Retrieve all albums belonging to the authenticated user."""
    return await service.get_user_albums(
        user_id=uuid.UUID(current_user.user_id)
    )


@router_album.get(
    "/{album_id}",
    response_model=AlbumResponse,
    status_code=status.HTTP_200_OK,
    summary="Get album details",
    description="""
    Retrieve a specific album by its ID, including all its images.
    
    - **Authorization**: User can only access their own albums.
    - **Includes**: All images belonging to this album.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "Album details retrieved successfully"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Album not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_album(
    request: Request,
    album_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """Retrieve a specific album by ID, including all its images."""
    return await service.get_album(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id
    )


@router_album.patch(
    "/{album_id}",
    response_model=AlbumResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an album",
    description="""
    Partially update an existing album. Only provided fields will be updated.
    
    - **Partial Update**: Only include fields you want to change.
    - **Authorization**: User can only update their own albums.
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        200: {"description": "Album updated successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Album not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def update_album(
    request: Request,
    album_id: uuid.UUID,
    data: AlbumUpdate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """Partially update an existing album."""
    return await service.update_album(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id,
        data=data
    )


@router_album.delete(
    "/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an album",
    description="""
    Permanently delete an album and all its images.
    
    - **Authorization**: User can only delete their own albums.
    - **Warning**: This action cannot be undone.
    - **Cascade**: All images in the album will be deleted.
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        204: {"description": "Album deleted successfully"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Album not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def delete_album(
    request: Request,
    album_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """Permanently delete an album and all its images."""
    await service.delete_album(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id
    )


# ============================================================
# Image Endpoints (within Albums)
# ============================================================

@router_image.post(
    "/{album_id}",
    response_model=List[ImageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload images to album",
    description="""
    Bulk upload images to a specific album.
    
    - **Formats**: Supported formats are JPEG, PNG, WebP.
    - **Size Limit**: Maximum 5MB per image.
    - **Auto-slug**: Slugs are auto-generated from album title.
    - **Cover Image**: First uploaded image becomes album cover (if none exists).
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        201: {"description": "Images uploaded successfully"},
        400: {"description": "Invalid file format or size exceeded"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Album not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def upload_images(
    request: Request,
    album_id: uuid.UUID,
    files: List[UploadFile] = File(..., description="Image files to upload (max 5MB each)"),
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """Bulk upload images to a specific album."""
    return await service.upload_images(
        user_id=uuid.UUID(current_user.user_id),
        album_id=album_id,
        files=files
    )


@router_image.get(
    "/",
    response_model=List[ImageResponse],
    status_code=status.HTTP_200_OK,
    summary="List all images",
    description="""
    Retrieve all images belonging to the authenticated user across all albums.
    
    - **Authorization**: User can only access their own images.
    - **Pagination**: Use limit and offset for pagination.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "List of images retrieved successfully"},
        401: {"description": "User is not authenticated"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_user_images(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """Retrieve all images belonging to the authenticated user."""
    return await service.get_user_images(
        user_id=uuid.UUID(current_user.user_id),
        limit=limit,
        offset=offset
    )


@router_image.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image",
    description="""
    Permanently delete an image by its ID.

    - **Authorization**: User can only delete their own images.
    - **Warning**: This action cannot be undone.
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        204: {"description": "Image deleted successfully"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Image not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def delete_image(
    request: Request,
    image_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """Delete an image."""
    await service.delete_image(uuid.UUID(current_user.user_id), image_id)
    return None
