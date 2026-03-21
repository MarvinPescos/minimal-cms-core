from app.infrastructure.database import TenantScopeRepository
from sqlalchemy import select
import uuid

from .models import ContentEntry, ContentType

class ContentEntryRepository(TenantScopeRepository[ContentEntry]):
    """"""

    def __init__(self, session):
        super().__init__(ContentEntry, session)

    # Get all contentEntry with 
    async def get_all_content_entry(self, tenant_id: uuid.UUID, content_type_id: uuid.UUID | None = None):

        query = (
            select(ContentEntry).
            where(ContentEntry.tenant_id == tenant_id)
        )

        if content_type_id:
            query = query.where(
                ContentEntry.content_type_id == content_type_id
            )
        
        result = await self.session.execute(query)
        return result.scalars().all()


class ContentTypeRepository(TenantScopeRepository[ContentType]):
    """"""

    def __init__(self, session):
        super().__init__(ContentType, session)