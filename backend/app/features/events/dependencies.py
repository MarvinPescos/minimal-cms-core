from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from .service import EventService

def get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
    """Dependency injection (provides EventService with database session)"""
    return EventService(db)