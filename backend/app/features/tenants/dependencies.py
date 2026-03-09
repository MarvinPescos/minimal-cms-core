from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from .service import TenantService, TenantMemberService


def get_tenant_service(db: AsyncSession = Depends(get_db)) -> TenantService:
    """Dependency injection for TenantService"""
    return TenantService(db)

def get_tenant_member_service(db: AsyncSession = Depends(get_db)) -> TenantMemberService:
    """Dependency injection for TenantMemberService"""
    return TenantMemberService(db)