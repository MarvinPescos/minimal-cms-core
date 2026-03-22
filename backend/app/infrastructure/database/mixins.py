from datetime import datetime, timezone


class SoftDeleteMixin:

    def _build_conditions(self, include_deleted=False, only_deleted=False, **kwargs):
        conditions = super()._build_conditions(**kwargs)
        if only_deleted:
            conditions.append(self.model.deleted_at.is_not(None))
        elif not include_deleted:
            conditions.append(self.model.deleted_at.is_(None))
        return conditions

    async def soft_delete(self, db_obj):
        db_obj.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return db_obj

    async def restore(self, db_obj):
        db_obj.deleted_at = None
        await self.session.flush()
        return db_obj


class PublishableMixin:

    def _build_conditions(self, published_only=False, **kwargs):
        conditions = super()._build_conditions(**kwargs)
        if published_only:
            conditions.append(self.model.is_published == True)
        return conditions