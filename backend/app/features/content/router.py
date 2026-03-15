from fastapi import APIRouter, Depends, status, Request
from typing import List
import uuid

from app.infrastructure.security import AuthenticatedUser, require_auth
from app.infrastructure.cache import limiter, RateLimits
from .schemas import (
    ContentTypeCreate, 
    ContentTypeUpdate,
    ContentTypeResponse
)
from .service import ContentTypeService
from .dependencies import get_content_type_service

router_content_type = APIRouter(prefix="/content/type", tags=["ContentTypes"])

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


