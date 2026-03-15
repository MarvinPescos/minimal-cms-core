from slugify import slugify
from app.infrastructure.database import BaseRepository
from app.infrastructure.database import TenantScopeRepository
from sqlalchemy import select
import uuid

from .models import Tenant, TenantMembers

class TenantRepository(BaseRepository[Tenant]):
    """Repository pattern for Tenant"""

    def __init__(self , session):
        super().__init__(Tenant, session)

    async def get_by_identifier(self, identifier: str) -> Tenant | None:
        try:
            parsed = uuid.UUID(str(identifier))
            condition = self.model.id == parsed
        except ValueError:
            condition = self.model.slug == identifier

        result = await self.session.execute(
            select(self.model).where(condition)
        )
        return result.scalar_one_or_none()

    async def generate_unique_slug(self, base_text: str, tenant_id: uuid.UUID | None = None) -> str:
        base_slug = slugify(base_text)
        slug = base_slug
        counter = 1

        while True:
            existing = await self.get_by_identifier(identifier=slug)

            if not existing: #if it not exist matik break then return ang slug
                break
            
            slug = f"{base_slug}-{counter}"
            counter +=1
        
        return slug
    
    # === Custom Methods ===

class TenantMembersRepository(TenantScopeRepository[TenantMembers]):
    """Repository pattern for TenantMembers"""

    def __init__(self, session):
        super().__init__(TenantMembers, session)

    # === Custom Methods ===
