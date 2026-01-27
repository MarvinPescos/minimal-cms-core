from app.infrastructure.database.user_repository import UserScopeRepository
from sqlalchemy import select, and_
from .models import Event
import uuid

class EventsRepository(UserScopeRepository[Event]):
    """Repository Pattern for events item access"""

    def __init__(self, session):
        super().__init__(Event, session)

    # ============ Custom Methods ============

        
    async def get_published_by_user(self, user_id: uuid.UUID, limit: int, offset: int):
        result = await self.session.execute(
            select(self.model)
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_published
                )
            )
            .order_by(self.model.start_at)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_published_event_by_slug(self, user_id: uuid.UUID, slug: str):
        """Get a single published event by slug for public access"""
        result = await self.session.execute(
            select(self.model)
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.slug == slug,
                    self.model.is_published
                )
            )
        )
        return result.scalar_one_or_none()
