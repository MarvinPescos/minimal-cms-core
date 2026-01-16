from app.infrastructure.database.user_repository import UserScopeRepository
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .models import Event

from app.infrastructure.observability import log
from app.infrastructure.database import DatabaseError

class EventsRepository(UserScopeRepository[Event]):
    """Repository Pattern for events item access"""

    def __init__(self, session):
        super().__init__(Event, session)

    # ============ Custom Methods ============

    async def get_by_slug(self, slug: str) -> Event | None:
        try:
            result = await self.session.execute(
                select(Event).
                where(Event.slug == slug)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="get_by_user_and_id",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to get by user and id {self.model_name}",
                original_error=e
            )
