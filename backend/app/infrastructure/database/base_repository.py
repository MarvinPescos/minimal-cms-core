from datetime import datetime, timezone
from typing import TypeVar, Generic, Type, Optional, Any, List
import uuid


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .exceptions import DatabaseError, IntegrityConstraintError

from app.infrastructure.observability.logging_setup import log

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """
        Generic repository with common crud operation.
        DRY!
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.session = session
        self.model = model
        self.model_name = model.__name__
    
    async def create(self, **data) -> ModelType:
        """Create new record"""
        try:
            db_obj = self.model(**data)
            self.session.add(db_obj)
            await self.session.flush()
            # No refresh - override if needed
            return db_obj
        except IntegrityError as e:
            log.error(
                "database.integrity_error",
                model=self.model_name,
                error=str(e.orig) if hasattr(e, 'orig') else str(e)
            )
            raise IntegrityConstraintError(
                f"Integrity constraint violated for {self.model_name}",
                original_error=e
            )
        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="create",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to create at {self.model_name}",
                original_error=e
            )
    
    async def get_by_id(self, id: uuid, include_deleted: bool = False) -> Optional[ModelType]:
        """Get record by ID"""
        try:
            query = select(self.model).where(self.model == id)
            if not include_deleted and hasattr(self.model, "deleted_at"):
                query = query.where(self.model.deleted_at.is_(None))
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="get_by_id",
                id=str(id),
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to fetch at {self.model_name}",
                original_error=e
            )
    
    async def get_all(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> List[ModelType]:
        """Get all in the model"""
        try:
            query = select(self.model).limit(limit).offset(offset)
            if not include_deleted and hasattr(self.model, 'deleted_at'):
                query = query.where(self.model.deleted_at.is_(None))
            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            log.error(
                "databse.error",
                model=self.model_name,
                operation="get_all",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to fetch all at {self.model_name}",
                original_error=e
            )
        
    async def update(self, db_obj: ModelType, **data ) -> ModelType:
        """Update a record"""
        try:
            for key, value in data.items():
                if hasattr(db_obj, key) and value is not None:
                    setattr(db_obj, key, value )
            await self.session.flush()
            return db_obj
        except IntegrityError as e:
            log.error(
                "database.integrity_error",
                model=self.model_name,
                operation="update",
                error=str(e.orig) if hasattr(e, 'orig') else str(e)
            )
            raise IntegrityConstraintError(
                f"Integrity constraint violated updating: {self.model_name}",
                original_error=e
            )
        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="update",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to update at {self.model_name}",
                original_error=e
            )
    
    async def delete(self, db_obj: ModelType):
        """Delete a record"""
        try:
            await self.session.delete(db_obj)
            await self.session.flush()
        except SQLAlchemyError as e:
            log.error(
                "database.error",
                model=self.model_name,
                operation="delete",
                error=str(e)
            )
            raise DatabaseError(
                f"Failed to delete at {self.model_name}",
                original_error=e
            )
    
    # === Soft Delete ===

    async def soft_delete(self, db_obj: ModelType) -> ModelType:
        """Soft delete a record by setting deleted_at"""
        db_obj.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return db_obj

    async def restore(self, db_obj: ModelType) -> ModelType:
        """Restore a soft-deleted record"""
        db_obj.deleted_at = None
        await self.session.flush()
        return db_obj



    


