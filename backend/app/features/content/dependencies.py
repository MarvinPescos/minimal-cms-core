from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from .service import ContentTypeService, ContentEntryService

def get_content_type_service(db: AsyncSession = Depends(get_db)) -> ContentTypeService:
    """"""
    return ContentTypeService(db)

def get_content_entry_service(db: AsyncSession = Depends(get_db)) -> ContentEntryService:
    """"""
    return ContentEntryService(db)