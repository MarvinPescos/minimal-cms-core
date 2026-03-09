from time import timezone
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone


from .tenant_scoped_repository import TenantScopeRepository, ModelType
from .exceptions import DatabaseError
from ..observability import log

class SoftDeleteRepository(TenantScopeRepository[ModelType]):

    def _build_conditions(
        self, 
        include_deleted: bool = False, 
        only_deleted: bool = False,
        **kwargs
    ) -> list:
        conditions = super()._build_conditions(**kwargs)

        if only_deleted:
            conditions.append(self.model.deleted_at.is_not(None))
        elif not include_deleted:
            conditions.append(self.model.deleted_at.is_(None))
        
        return conditions

    async def soft_delete(self, db_obj: ModelType) -> ModelType:
        db_obj.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return db_obj

    async def restore(self, db_obj: ModelType) -> ModelType:
        db_obj.deleted_at = None
        await self.session.flush()
        return db_obj



