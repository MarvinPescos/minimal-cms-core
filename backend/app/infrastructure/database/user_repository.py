from slugify import slugify
from typing import List
from sqlalchemy import select, and_
import uuid


from sqlalchemy.exc import SQLAlchemyError

from .base_repository import ModelType, BaseRepository
from .exceptions import DatabaseError
from ..observability import log


class UserScopeRepository(BaseRepository[ModelType]):

    async def get_one(
        self, 
        tenant_id: uuid.UUID,
        identifier: str | uuid.UUID,
        user_id: uuid.UUID | None = None,
        content_type_id: uuid.UUID | None = None,
        include_deleted: bool = False,
        published_only: bool = False
    ) -> ModelType | None:  
        """
        Get single item by ID or slug, optionally scoped by user.

        - tenant_id: scope to this tenant
        - identifier: UUID string or slug
        - content_type_id: scope to this content_type 
        - include_deleted: if False, excludes soft-deleted records
        - published_only: if True, only return published records
        """
        try:
            conditions = []

            try:
                parsed = uuid.UUID(str(identifier))
                conditions.append(self.model.id == parsed)
            except ValueError:
                conditions.append(self.model.slug == identifier)

            conditions.append(self.model.tenant_id == tenant_id)

            if content_type_id:
                conditions.append(self.model.content_type_id == content_type_id)

            if not include_deleted and hasattr(self.model, "deleted_at"):
                conditions.append(self.model.deleted_at.is_(None))

            if published_only and hasattr(self.model, "is_published"):
                conditions.append(self.model.is_published == True)
            
            result = await self.session.execute(
                select(self.model).where(and_(*conditions))
            )
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="get_one",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to get {self.model_name}",
                original_error=e
            )

    async def get_many(
        self,
        tenant_id: uuid.UUID,
        content_type_id: uuid.UUID | None = None,
        include_deleted: bool = False,
        only_deleted: bool = False,
        published_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[ModelType]:
        """"""
        try:
            conditions = []

            conditions.append(self.model.tenant_id == tenant_id)

            if content_type_id:
                conditions.append(self.model.content_type_id == content_type_id)
            
            if hasattr(self.model, "deleted_at"):
                if only_deleted:
                    conditions.append(self.model.deleted_at.is_not(None))
                elif not include_deleted:
                    conditions.append(self.model.deleted_at.is_(None))

            if published_only and hasattr(self.model, "is_published"):
                conditions.append(self.model.is_published == True)
            
            result = await self.session.execute(
                select(self.model).where(and_(*conditions))
                .limit(limit).offset(offset)
            )

            return result.scalars().all()
        
        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="get_many",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to list {self.model_name}",
                original_error=e
            )

    async def generate_unique_slug(self, base_text: str, tenant_id: uuid.UUID | None = None) -> str:
        base_slug = slugify(base_text)
        slug = base_slug
        counter = 1

        while True:
            existing = await self.get_one(tenant_id, slug)

            if not existing: #if it not exist matik break then return ang slug
                break
            
            slug = f"{base_slug}-{counter}"
            counter +=1
        
        return slug

