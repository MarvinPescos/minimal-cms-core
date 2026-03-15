from fastapi import APIRouter, Depends, status, Request
from typing import List, Required
import uuid

from app.infrastructure.security import require_admin, AuthenticatedUser, require_auth
from app.infrastructure.cache import limiter, RateLimits
from .schemas import ( 
    StaffAccountCreate,
    StaffAccountResponse,
    StaffAccountUpdate,
    TenantCreate,
    TenantResponse,
    TenantUpdate
)
from .service import TenantService, TenantMemberService
from .dependencies import get_tenant_service, get_tenant_member_service

router_tenant = APIRouter(prefix="/tenants", tags=["Tenants"])
router_tenant_member = APIRouter(prefix="/tenant/members", tags=["Tenant Members"])


@router_tenant.get(
    "/",
    response_model=List[TenantResponse],
    status_code=status.HTTP_200_OK,
    summary="List all Tenants"
)
@limiter.limit(RateLimits.READ_HEAVY)
async def list_all_tenants(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_admin),
    service: TenantService = Depends(get_tenant_service)
):
    """Get all tenants"""
    return await service.get_all_tenants()

@router_tenant.get(
    "/{identifier}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an specific Tenant"
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_tenant(
    request:Request,
    identifier: uuid.UUID | str,
    current_user: AuthenticatedUser = Depends(require_admin),
    service: TenantService = Depends(get_tenant_service)
):
    """Get an tenant"""
    return await service.get_tenant(identifier=identifier)

@router_tenant.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Creaete a tenant"
)
@limiter.limit(RateLimits.STANDARD)
async def create_tenant(
    request: Request,
    data: TenantCreate,
    current_user: AuthenticatedUser = Depends(require_admin),
    service: TenantService = Depends(get_tenant_service)
):
    """Create a tenant"""
    return await service.create_tenant(data=data)


@router_tenant.patch(
    "/{identifier}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a tenant"
)
@limiter.limit(RateLimits.STANDARD)
async def update_tenant(
    request: Request,
    identifier: uuid.UUID | str,
    data: TenantUpdate,
    current_user: AuthenticatedUser = Depends(require_admin),
    service: TenantService = Depends(get_tenant_service)
):
    """Partially update an existing tenant"""
    return await service.update_tenant(identifier= identifier, data=data)    

# <===-=-=-=-=-=-=-=-=-=-=-======-=-=-=-=-=-=-=-=-=-=-=-===>

@router_tenant_member.get(
    "/",
    response_model=List[StaffAccountResponse],
    status_code=status.HTTP_200_OK,
    summary="List all Tenant Member"   
)
@limiter.limit(RateLimits.READ_HEAVY)
async def list_all_tenant_members(
    request: Request,
    tenant_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: TenantMemberService = Depends(get_tenant_member_service)
):
    """Get all tenant member"""
    return await service.get_all_tenant_members(tenant_id)

@router_tenant_member.get(
    "/{identifier}",
    response_model=StaffAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a tenant Member"
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_tenant_member(
    request: Request,
    tenant_id: uuid.UUID,
    identifier: str | uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: TenantMemberService = Depends(get_tenant_member_service)
):
    """Get a tenant member"""
    return await service.get_tenant_member(tenant_id, identifier)

@router_tenant_member.post(
    "/",
    response_model=StaffAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tenant member"
)
@limiter.limit(RateLimits.STANDARD)
async def create_tenant_member(
    request: Request,
    tenant_id: uuid.UUID,
    data: StaffAccountCreate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: TenantMemberService = Depends(get_tenant_member_service)
):
    """Create a tenant"""
    return await service.create_account(tenant_id, data)

@router_tenant_member.patch(
    "/",
    response_model=StaffAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a tenant member"
)
@limiter.limit(RateLimits.STANDARD)
async def update_tenant_member(
    request: Request,
    tenant_id: uuid.UUID,
    tenant_member_id: uuid.UUID,
    data: StaffAccountUpdate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: TenantMemberService = Depends(get_tenant_member_service)
):
    """Update a tenant"""
    return await service.update_account(tenant_id, tenant_member_id, data)

@router_tenant_member.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tenant member"
)
@limiter.limit(RateLimits.STANDARD)
async def delete_tenant_member(
    request: Request,
    tenant_id: uuid.UUID,
    tenant_member_id: uuid.UUID,
    current_user: AuthenticatedUser =  Depends(require_auth),
    service: TenantMemberService = Depends(get_tenant_member_service)
):
    """Delete a tenant"""
    return await service.delete_account(tenant_id, tenant_member_id)