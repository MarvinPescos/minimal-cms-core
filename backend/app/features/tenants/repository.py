from app.infrastructure.database import TenantScopeRepository
from sqlalchemy import select
import uuid

from .models import Tenant, TenantMembers

class TenantRepository(TenantScopeRepository[Tenant]):
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
    
    # === Custom Methods ===

class TenantMembersRepository(TenantScopeRepository[TenantMembers]):
    """Repository pattern for TenantMembers"""

    def __init__(self, session):
        super().__init__(TenantMembers, session)

    # === Custom Methods ===
