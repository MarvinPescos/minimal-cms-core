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


@router_album.get(
    "/",
    response_model=List[AlbumResponse],
    status_code=status.HTTP_200_OK,
    summary="List all albums",
    description="""
    Retrieve all albums belonging to a specific tenant.
    
    - **Authorization**: User must be authenticated.
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
    tenant_id: uuid.UUID,
    is_published: bool | None = None,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    List all albums for a given tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        is_published: Optional filter for publication status.
        current_user: The authenticated user making the request.
        service: The album management service.

    Returns:
        List of `AlbumResponse` objects.
    """
    return await service.get_tenant_albums(tenant_id, is_published)



@router_album.get(
    "/{identifier}",
    response_model=AlbumResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single album",
    description="""
    Retrieve a specific album by its ID or slug within a tenant.
    
    - **Authorization**: User must be authenticated.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "Album retrieved successfully"},
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
    tenant_id: uuid.UUID,
    identifier: str | uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Fetch a single album by ID or slug within a tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        identifier: UUID or slug identifying the album.
        current_user: The authenticated user making the request.
        service: The album management service.

    Returns:
        The matching `AlbumResponse`.

    Raises:
        NotFoundError: If the album does not exist.
    """
    return await service.get_album(tenant_id, identifier)



@router_album.post(
    "/",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new album",
    description="""
    Create a new album for a tenant.
    
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
    tenant_id: uuid.UUID,
    data: AlbumCreate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Create a new tenant-scoped album.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant that will own the album.
        data: Payload containing the album definition.
        current_user: The authenticated user making the request.
        service: The album management service.

    Returns:
        The created `AlbumResponse`.

    Raises:
        BadRequestError: If the payload is invalid.
        ConflictError: If the album title violates uniqueness constraints.
    """
    return await service.create_album(tenant_id, data)



@router_album.patch(
    "/{identifier}",
    response_model=AlbumResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an album",
    description="""
    Partially update an existing album. Only provided fields will be updated.
    
    - **Partial Update**: Only include fields you want to change.
    - **Authorization**: User must be authenticated.
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
    tenant_id: uuid.UUID,
    identifier: str | uuid.UUID,
    data: AlbumUpdate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Partially update an existing album.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        identifier: UUID or slug identifying the album.
        data: Partial update payload.
        current_user: The authenticated user making the request.
        service: The album management service.

    Returns:
        The updated `AlbumResponse`.

    Raises:
        NotFoundError: If the album does not exist.
        ConflictError: If updates violate constraints.
    """
    return await service.update_album(
        tenant_id=tenant_id,
        identifier=identifier,
        data=data
    )


@router_album.delete(
    "/{identifier}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an album",
    description="""
    Permanently delete an album and all its images.
    
    - **Authorization**: User must be authenticated.
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
    tenant_id: uuid.UUID,
    identifier: str | uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: AlbumService = Depends(get_album_service)
):
    """
    Permanently delete a tenant-scoped album.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        identifier: UUID or slug identifying the album.
        current_user: The authenticated user making the request.
        service: The album management service.

    Raises:
        NotFoundError: If the album does not exist.
    """
    await service.delete_album(tenant_id=tenant_id, identifier=identifier)


# ============================================================
# Image Endpoints (within Albums)
# ============================================================

@router_image.post(
    "/{album_identifier}",
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
    tenant_id: uuid.UUID,
    album_identifier: str | uuid.UUID,
    files: List[UploadFile] = File(..., description="Image files to upload (max 5MB each)"),
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """
    Upload multiple images to an album and create database records.

    Args:
        tenant_id: UUID of the tenant owning the album.
        album_identifier: UUID or slug of the target album.
        files: List of uploaded files.
        current_user: The authenticated user making the request.
        service: The image management service.

    Returns:
        List of `ImageResponse` objects.

    Raises:
        NotFoundError: If the album does not exist.
        BadRequestError: If files are invalid or too large.
    """
    return await service.upload_images(
        tenant_id,
        album_identifier=album_identifier,
        files=files
    )


@router_image.get(
    "/{album_identifier}",
    response_model=List[ImageResponse],
    status_code=status.HTTP_200_OK,
    summary="List all images in a specific album",
    description="""
    Retrieve all images belonging to a specific album within a tenant.
    
    - **Authorization**: User must be authenticated.
    - **Pagination**: Use limit and offset for pagination.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "List of images retrieved successfully"},
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
async def get_images_in_album(
    request: Request,
    tenant_id: uuid.UUID,
    album_identifier: str,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """
    List all images within a specific album.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        album_identifier: UUID or slug of the album.
        limit: Maximum number of records to return.
        offset: Number of records to skip.
        current_user: The authenticated user making the request.
        service: The image management service.

    Returns:
        List of `ImageResponse` objects.

    Raises:
        NotFoundError: If the album does not exist.
    """
    return await service.get_images_in_album(
        tenant_id,
        album_identifier,
        limit=limit,
        offset=offset
    )


@router_image.get(
    "/",
    response_model=List[ImageResponse],
    status_code=status.HTTP_200_OK,
    summary="List all public images",
    description="""
    Retrieve all images from published albums within a tenant.
    
    - **Authorization**: User must be authenticated.
    - **Pagination**: Use limit and offset for pagination.
    - **Scopes**: Only returns images from published albums.
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
async def get_tenant_images(
    request: Request,
    tenant_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """
    List all images from published albums for a tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        limit: Maximum number of records to return.
        offset: Number of records to skip.
        current_user: The authenticated user making the request.
        service: The image management service.

    Returns:
        List of `ImageResponse` objects.
    """
    return await service.get_public_images(
        tenant_id,
        limit=limit,
        offset=offset
    )


@router_image.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image",
    description="""
    Permanently delete an image by its ID.

    - **Authorization**: User must be authenticated.
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
    tenant_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ImageService = Depends(get_image_service)
):
    """
    Permanently delete a single image.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant owning the image.
        image_id: UUID of the image to delete.
        current_user: The authenticated user making the request.
        service: The image management service.

    Raises:
        NotFoundError: If the image does not exist.
    """
    await service.delete_image(tenant_id, image_id)
    return None
