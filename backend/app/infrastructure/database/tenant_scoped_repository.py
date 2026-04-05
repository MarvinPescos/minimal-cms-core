from typing import List
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
import uuid

from .base_repository import ModelType, BaseRepository
from .exceptions import DatabaseError
from ..observability import log


class TenantScopeRepository(BaseRepository[ModelType]):

    def _build_conditions(
        self, 
        tenant_id: uuid.UUID, 
        identifier: str | uuid.UUID | None = None,
        **kwargs
    ) -> list:
        conditions = [self.model.tenant_id == tenant_id]

        if identifier:
            try:
                parsed = uuid.UUID(str(identifier))
                conditions.append(self.model.id == parsed)
            except ValueError:
                conditions.append(self.model.slug == identifier )
        
        return conditions


    async def get_one(
        self, 
        tenant_id: uuid.UUID,
        identifier: str | uuid.UUID | None = None,
        **kwargs
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
            conditions = self._build_conditions(
                tenant_id=tenant_id,
                identifier=identifier,
                **kwargs,
            )
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
        limit: int = 100,
        offset: int = 0,
        **kwargs
    ) -> List[ModelType]:
        """"""
        try:
            conditions = self._build_conditions(
                tenant_id=tenant_id, 
                identifier=None,
                **kwargs)
            result = await self.session.execute(
                select(self.model)
                .where(and_(*conditions))
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

