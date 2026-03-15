from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from .service import ContentTypeService

def get_content_type_service(db: AsyncSession = Depends(get_db)) -> ContentTypeService:
    """"""
    return ContentTypeService(db)
    