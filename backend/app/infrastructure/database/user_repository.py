from slugify import slugify
from typing import List
from sqlalchemy import select, and_
import uuid


from sqlalchemy.exc import SQLAlchemyError

from .base_repository import ModelType, BaseRepository
from .exceptions import DatabaseError
from ..observability import log


class UserScopeRepository(BaseRepository[ModelType]):

    async def get_by_user_and_id(self, user_id: uuid.UUID, item_id: uuid.UUID):
        """Get single item scoped for user"""
        try:
            result = await self.session.execute(
                select(self.model).
                where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.id == item_id
                    )
                )
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

    async def get_all_by_user_id(self, user_id: uuid.UUID, limit: int = 100, offset: int = 0) ->  List[ModelType]:
        """Get all item by user ID with pagination ofc"""
        try:
            result = await self.session.execute(
                select(self.model).
                where(self.model.user_id == user_id).
                limit(limit).
                offset(offset)
            )
            return result.scalars().all()

        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="get_all_by_user_id",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to get all by user id {self.model_name}",
                original_error=e
            )
    
    # TODO pagination
    
    async def get_by_slug(self, slug: str, user_id: uuid.UUID | None = None) -> ModelType | None:
        """Get record bu slug"""
        try:
            query = select(self.model).where(self.model.slug == slug)

            if user_id:
                query = query.where(self.model.user_id == user_id)
                
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="get_by_slug",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to get by slug {self.model_name}",
                original_error=e
            )

    async def generate_unique_slug(self, base_text: str, user_id: uuid.UUID | None = None) -> str:
        base_slug = slugify(base_text)
        slug = base_slug
        counter = 1

        while True:
            existing = await self.get_by_slug(slug, user_id)

            if not existing: #if it not exist matik break then return ang slug
                break
            
            slug = f"{base_slug}-{counter}"
            counter +=1
        
        return slug
