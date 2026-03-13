from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.infrastructure.database import IntegrityConstraintError, DatabaseError
from app.shared.errors import BaseAppException, ConflictError, BadRequestError, NotFoundError
from app.infrastructure.observability import log

from .models import ContentEntry, ContentType
from .repository import ContentEntryRepository, ContentTypeRepository

class ContentEntryService:
    """"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContentEntryRepository(session)
    

    async def get_all_content_entry(self, tenant_id: uuid.UUID) -> List[ContentEntry]:
        """"""
        log.info("content_entry.get.all", tenant_id=tenant_id)
        return await self.repo.get_many()
