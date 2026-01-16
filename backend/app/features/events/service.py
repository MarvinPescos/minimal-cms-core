from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify
import uuid

from app.infrastructure.database import IntegrityConstraintError, DatabaseError
from .repository import EventsRepository
from .schemas import EventCreate, EventUpdate
from .models import Event
from app.shared.errors.exceptions import BaseAppException, ConflictError, NotFoundError
from app.infrastructure.observability import log

class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EventsRepository(session)

    #  === Read Operations ===

    async def get_user_events(self, user_id: uuid.UUID) -> List[Event]:
        """
            Retrieve all events belonging to this user
        """

        log.info("events.fetch.all", user_id=user_id)
        return await self.repo.get_all_by_user_id(user_id=user_id)

    async def get_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> Event:
        """
            Retrieve single events belonging to this user
        """
        event = await self.repo.get_by_user_and_id(user_id=user_id, item_id=event_id)

        if not event:
            raise NotFoundError("Event not found")

        log.info(
            "events.fetch",
            user_id=user_id,
            event_id=event_id,
        )

        return event

    #  === Write Operations ===

    async def add_event(self, user_id: uuid.UUID, data: EventCreate) -> Event:
        """
            Add a new event to the users events
        """
        log.info(f"User: {user_id} is adding event '{data.title}'")
        try:
            slug = slugify(data.title)

            base_slug = slug
            counter = 1

            # TODO Change this hahhatdog

            while await self.repo.get_by_slug(slug):  # You'd need this repo method
                slug = f"{base_slug}-{counter}"
                counter += 1

            log.info(
                "event.create",
                user_id=user_id,
                event_name=data.title
            )
            return await self.repo.create(user_id=user_id, slug=slug,**data.model_dump())

        except IntegrityConstraintError as e:
            log.warning(
                "event.create.integrity_error",
                user_id=str(user_id),
                event_title=data.title,
                error=str(e)
            )
            raise ConflictError("Creates violates constraints")
        except DatabaseError as e:
            log.error(
                "event.database.error",
                user_id=str(user_id),
                error=str(e),
            )
            raise BaseAppException("Failed to save event")

    async def update_event(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        data: EventUpdate
    ) -> Event:
        """
            Partially update an existing shopping item with ownership verification
        """
        log.info(f"User: {user_id} is updating event '{data.title}'")

        event = await self.get_event(user_id=user_id, event_id=event_id)

        try:
            updated_data = data.model_dump(exclude_unset=True)
            log.info(
                "event.update",
                user_id=user_id,
                event_id=str(event_id),
                updated_field = list(updated_data.keys())
            )
            return await self.repo.update(event, **updated_data)

        except IntegrityConstraintError as e:
            log.warning(
                "event.update.integrity_error",
                user_id=str(user_id),
                event_title=data.title,
                error=str(e)
            )
            raise ConflictError("Update violates constraints")
        except DatabaseError as e:
            log.error(
                "event.database.error",
                user_id=str(user_id),
                error=str(e),
            )
            raise BaseAppException("Failed to update event")


    async def delete_event(self, user_id: uuid.UUID, event_id: uuid.UUID ) -> None:
        "Permanently delete a fridge item after verifying ownership."

        event = await self.get_event(user_id=user_id, event_id=event_id)
        log.info(f"User: {user_id} is deleting event '{event.title}'")

        try:
            log.info(
                "event.deleted",
                user_id=str(user_id),
                event_id=str(event_id),
                title=event.title,
            )
            await self.repo.delete(event)
        except DatabaseError as e:
            log.error(
                "event.database.error",
                user_id=str(user_id),
                event_id=str(event_id),
                error=str(e)
            )
            raise BaseAppException("Failed to delete event")
