from app.infrastructure.database import TenantScopeRepository
from sqlalchemy import select
import uuid

from .models import ContentEntry, ContentType

class ContentEntryRepository(TenantScopeRepository[ContentEntry]):
    """"""

    def __init__(self, session):
        super().__init__(ContentEntry, session)


class ContentTypeRepository(TenantScopeRepository[ContentType]):
    """"""

    def __init__(self, session):
        super().__init__(ContentType, session)