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
    """Get all content type"""
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
    """Get content type"""
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
    """Create content type"""
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
    """Partially update an existing tenant"""
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
    """Delete a tenant"""
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
    """Get all content type"""
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
    """Get content type"""
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
    """Create content type"""
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
    """Partially update an existing tenant"""
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
    """Delete a tenant"""
    return await service.delete_content_entry(tenant_id, identifier)