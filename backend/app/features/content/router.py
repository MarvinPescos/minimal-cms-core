from fastapi import APIRouter, Depends, status, Request
from typing import List
import uuid

from app.infrastructure.security import AuthenticatedUser, require_auth
from app.infrastructure.cache import limiter, RateLimits
from .schemas import (
    ContentTypeCreate, 
    ContentTypeUpdate,
    ContentTypeResponse,
    ContentEntryCreate,
    ContentEntryUpdate,
    ContentEntryResponse,
)
from .service import ContentTypeService, ContentEntryService
from .dependencies import get_content_type_service, get_content_entry_service

router_content_type = APIRouter(prefix="/content/type", tags=["ContentTypes"])
router_content_entry = APIRouter(prefix="/content/entry", tags=["ContentEntry"])

@router_content_type.get(
    "/",
    response_model=List[ContentTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="List all created Content Type"
)
@limiter.limit(RateLimits.READ_HEAVY)
async def list_all_content_type(
    request: Request,
    tenant_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentTypeService = Depends(get_content_type_service)
):
    """
    List all content types for a given tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        limit: Maximum number of records to return.
        offset: Number of records to skip.
        current_user: The authenticated user making the request.
        service: The content type management service.

    Returns:
        List of `ContentTypeResponse` objects.
    """
    return await service.get_all_content_type(tenant_id)


@router_content_type.get(
    "/{identifier}",
    response_model=ContentTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get created Content Type"
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_content_type(
    request: Request,
    tenant_id: uuid.UUID,
    content_type_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentTypeService = Depends(get_content_type_service)
):
    """
    Fetch a single content type by ID within a tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        content_type_id: UUID of the content type.
        current_user: The authenticated user making the request.
        service: The content type management service.

    Returns:
        The matching `ContentTypeResponse`.

    Raises:
        NotFoundError: If the content type does not exist.
    """
    return await service.get_content_type(tenant_id, content_type_id)

@router_content_type.post(
    "/",
    response_model=ContentTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create content type"
)
@limiter.limit(RateLimits.STANDARD)
async def create_content_type(
    request:Request,
    tenant_id: uuid.UUID,
    data: ContentTypeCreate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentTypeService = Depends(get_content_type_service)
):
    """
    Create a new tenant-scoped content type.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant owning the content type.
        data: Payload containing the content type definition.
        current_user: The authenticated user making the request.
        service: The content type management service.

    Returns:
        The created `ContentTypeResponse`.

    Raises:
        ConflictError: If naming constraints are violated.
    """
    return await service.create_content_type(tenant_id, data)

@router_content_type.patch(
    "/{id}",
    response_model=ContentTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a content type"
)
@limiter.limit(RateLimits.STANDARD)
async def update_content_type(
    request: Request,
    tenant_id: uuid.UUID,
    content_type_id: uuid.UUID,
    data: ContentTypeUpdate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentTypeService = Depends(get_content_type_service)
):
    """
    Partially update an existing content type.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        content_type_id: UUID of the content type to update.
        data: Partial update payload.
        current_user: The authenticated user making the request.
        service: The content type management service.

    Returns:
        The updated `ContentTypeResponse`.

    Raises:
        NotFoundError: If the content type does not exist.
        ConflictError: If updates violate constraints.
    """
    return await service.update_content_type(tenant_id, content_type_id,data)  

@router_content_type.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tenant member"
)
@limiter.limit(RateLimits.STANDARD)
async def delete_content_type(
    request: Request,
    tenant_id: uuid.UUID,
    content_type_id: uuid.UUID,
    current_user: AuthenticatedUser =  Depends(require_auth),
    service: ContentTypeService = Depends(get_content_type_service)
):
    """
    Permanently delete a tenant-scoped content type.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        content_type_id: UUID of the content type to delete.
        current_user: The authenticated user making the request.
        service: The content type management service.

    Raises:
        NotFoundError: If the content type does not exist.
    """
    return await service.delete_content_type(tenant_id, content_type_id)


# ==============================

@router_content_entry.get(
    "/",
    response_model=List[ContentEntryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all created Content Entry"
)
@limiter.limit(RateLimits.READ_HEAVY)
async def list_all_content_entry(
    request: Request,
    tenant_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentEntryService = Depends(get_content_entry_service)
):
    """
    List all content entries for a given tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        limit: Maximum number of records to return.
        offset: Number of records to skip.
        current_user: The authenticated user making the request.
        service: The content entry management service.

    Returns:
        List of `ContentEntryResponse` objects.
    """
    return await service.get_all_content_entry(tenant_id)


@router_content_entry.get(
    "/{identifier}",
    response_model=ContentEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get created Content Type"
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_content_entry(
    request: Request,
    tenant_id: uuid.UUID,
    identifier: uuid.UUID | str,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentEntryService = Depends(get_content_entry_service)
):
    """
    Fetch a single content entry by ID or slug within a tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        identifier: UUID or slug identifying the entry.
        current_user: The authenticated user making the request.
        service: The content entry management service.

    Returns:
        The matching `ContentEntryResponse`.

    Raises:
        NotFoundError: If the entry does not exist.
    """
    return await service.get_content_entry(tenant_id, identifier)

@router_content_entry.post(
    "/",
    response_model=ContentEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create content entry"
)
@limiter.limit(RateLimits.STANDARD)
async def create_content_entry(
    request:Request,
    tenant_id: uuid.UUID,
    content_type_identifier: uuid.UUID | str,
    data: ContentEntryCreate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentEntryService = Depends(get_content_entry_service)
):
    """
    Create a new content entry for a tenant.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant owning the entry.
        content_type_identifier: ID or slug of the associated content type.
        data: Payload containing the entry definition.
        current_user: The authenticated user making the request.
        service: The content entry management service.

    Returns:
        The created `ContentEntryResponse`.

    Raises:
        NotFoundError: If the content type does not exist.
        BadRequestError: If the payload fails schema validation.
    """
    return await service.create_content_entry(tenant_id, content_type_identifier, data, current_user.user_id)

@router_content_entry.patch(
    "/",
    response_model=ContentEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a content entry"
)
@limiter.limit(RateLimits.STANDARD)
async def update_content_entry(
    request: Request,
    tenant_id: uuid.UUID,
    identifier: uuid.UUID | str,
    data: ContentEntryUpdate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: ContentEntryService = Depends(get_content_entry_service)
):
    """
    Partially update an existing content entry.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        identifier: UUID or slug identifying the entry to update.
        data: Partial update payload.
        current_user: The authenticated user making the request.
        service: The content entry management service.

    Returns:
        The updated `ContentEntryResponse`.

    Raises:
        NotFoundError: If the entry does not exist.
        BadRequestError: If the updated JSON payload fails schema validation.
    """
    return await service.update_content_entry(tenant_id, identifier, data, current_user.user_id)

@router_content_entry.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tenant member"
)
@limiter.limit(RateLimits.STANDARD)
async def delete_content_entry(
    request: Request,
    tenant_id: uuid.UUID,
    identifier: uuid.UUID | str,
    current_user: AuthenticatedUser =  Depends(require_auth),
    service: ContentEntryService = Depends(get_content_entry_service)
):
    """
    Permanently delete a tenant-scoped content entry.

    Args:
        request: The fastAPI request object.
        tenant_id: UUID of the tenant to scope the query to.
        identifier: UUID or slug identifying the entry to delete.
        current_user: The authenticated user making the request.
        service: The content entry management service.

    Raises:
        NotFoundError: If the entry does not exist.
    """
    return await service.delete_content_entry(tenant_id, identifier)