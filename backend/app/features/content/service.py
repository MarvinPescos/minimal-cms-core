from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import jsonschema

from app.infrastructure.database import IntegrityConstraintError, DatabaseError
from app.shared.errors import BaseAppException, ConflictError, BadRequestError, NotFoundError
from app.infrastructure.observability import log

from .models import ContentEntry, ContentType
from .repository import ContentEntryRepository, ContentTypeRepository
from .schemas import ContentTypeCreate, ContentTypeUpdate, ContentEntryCreate, ContentEntryUpdate

class ContentTypeService:
    """"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContentTypeRepository(session)
    

    async def get_all_content_type(self, tenant_id: uuid.UUID) -> List[ContentType]:
        """"""
        log.info("content.type.get.all", tenant_id=tenant_id)
        return await self.repo.get_many(tenant_id)

    async def get_content_type(self, tenant_id:uuid.UUID, content_type_id: uuid.UUID) -> ContentType:
        """"""
        content_type = await self.repo.get_one(tenant_id, content_type_id)

        if not content_type:
            raise NotFoundError("Content type not found")
        
        log.info(
            "content.type.get",
            tenant_id=tenant_id,
            identifier=content_type_id
        )

        return content_type
    
    async def create_content_type(self, tenant_id: uuid, data: ContentTypeCreate) -> ContentType:
        """"""
        try:
        
            content_type = await self.repo.create(tenant_id=tenant_id, **data.model_dump())

            log.info(
                "content.type.create",
                name=content_type.name
            )

            return content_type
        
        except IntegrityConstraintError as e:
            log.warning(
                "content.type.create.integrity_error",
                name=data.name,
                error=str(e)
            )
            raise ConflictError("Create violates constraints")
        except DatabaseError as e:
            log.error(
                "content.database.error",
                error=str(e),
            )
            raise BaseAppException("Failed to save content") 

    async def update_content_type(self, tenant_id: uuid.UUID, content_type_id: uuid.UUID, data: ContentTypeUpdate) -> ContentType:
        """"""  
        content_type = await self.get_content_type(tenant_id, content_type_id)
        try:
            updated_data = data.model.dump(exclude_unset=True)
            log.info(
                "content.type.update",
                tenant_id=tenant_id,
                content_type_id=content_type_id,
                updated_field=list(updated_data.keys())
            )
            return await self.repo.update(content_type, **updated_data)
        except IntegrityConstraintError as e:
            log.warning(
                "content.type.update.integrity_error",
                tenant_id=tenant_id,
                content_type_id=content_type_id,
                error=str(e)
            )
            raise ConflictError("Update violates constraints")
        except DatabaseError as e:
            log.error(
                "content.type.database.error",
                tenant_id=tenant_id,
                content_type_id=content_type_id,
                error=str(e),
            )
            raise BaseAppException("Failed to update tenant content type")

    async def delete_content_type(self, tenant_id: uuid.UUID, content_type_id: uuid.UUID) -> None:        
        content_type = await self.get_content_type(tenant_id, content_type_id)

        try:
            log.info(
                "content.type.deleted",
                tenant_id=tenant_id,
                content_type_id=content_type_id
            )
            await self.repo.delete(content_type)
        except DatabaseError as e:
            log.error(
                "content.type.error",
                tenant_id=tenant_id,
                content_type_id=content_type_id,
                error=str(e)
            )
            raise BaseAppException(f"{e}")

class ContentEntryService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContentEntryRepository(session)
        self.content_type_repo = ContentTypeRepository(session)


    async def get_all_content_entry(self, tenant_id: uuid.UUID, content_type_id: uuid.UUID | None = None) -> List[ContentEntry]:
        """"""
        log.info("content.entry.get.all", tenant_id=tenant_id, content_type_id=content_type_id)
        return await self.repo.get_all_content_entry(tenant_id, content_type_id)

    async def get_one_content_entry(self, tenant_id: uuid.UUID, identifier: uuid.UUID | str) -> ContentEntry:
        """"""
        log.info("content.entry.get.one")
        entry = await self.repo.get_one(tenant_id, identifier)

        if not entry:
            raise NotFoundError("Content entry not found")

        return entry
    
    async def create_content_entry(
        self, 
        tenant_id: uuid.UUID, 
        content_type_identifier: uuid.UUID | str, 
        data: ContentEntryCreate,
        user_id: str
    ) -> ContentEntry:
        """"""
        content_type = await self.content_type_repo.get_one(tenant_id, content_type_identifier)
        if not content_type:
            raise NotFoundError("Content type was not found")

        try:
            jsonschema.validate(instance=data.data, schema=content_type.json_schema)
        except jsonschema.ValidationError as e:
            # Change this to more user friendly error message
            raise BadRequestError(f" Does not match schema: {e.message}")

        try: 
            slug = await self.repo.generate_unique_slug(data.title, tenant_id)

            entry = await self.repo.create(
                tenant_id=tenant_id,
                content_type_id=content_type.id,
                created_by=uuid.UUID(user_id),
                slug=slug,
                **data.model_dump()
            )

            log.info(
                "content.entry.create",
                title=entry.title
            )

            return entry

        except IntegrityConstraintError as e:
            log.warning(
                "content.entry.create.integrity_error",
                title=data.title,
                error=str(e)
            )
            raise ConflictError("Create violates constraints")
        except DatabaseError as e:
            log.error(
                "content.database.error",
                error=str(e),
            )
            raise BaseAppException("Failed to save content entry") 
    
    async def update_content_entry(
        self, 
        tenant_id: uuid.UUID, 
        identifier: uuid.UUID | str, 
        data: ContentEntryUpdate, 
        user_id: str
    ) -> ContentEntry:
        """"""
        entry = await self.get_one_content_entry(tenant_id, identifier)
 
        updated_data = data.model_dump(exclude_unset=True)

        if "data" in updated_data:
            content_type = await self.content_type_repo.get_one(tenant_id, entry.content_type_id)
            try:
                jsonschema.validate(instance=updated_data["data"], schema=content_type.json_schema)
            except jsonschema.ValidationError as e:
                # Change this to more user friendly error message
                raise BadRequestError(f" Does not match schema: {e.message}")
        
        try:            
            updated_data["updated_by"] = uuid.UUID(user_id)

            log.info(
                "content.entry.update",
                title=entry.title
            )

            return await self.repo.update(entry, **updated_data)

        except IntegrityConstraintError as e:
            log.warning(
                "content.entry.update.integrity_error",
                identifier=str(identifier),
                error=str(e)
            )
            raise ConflictError("Update violates constraints")
        except DatabaseError as e:
            log.error(
                "content.database.error",
                error=str(e),
            )
            raise BaseAppException("Failed to update content entry") 
        
    async def delete_content_entry(self, tenant_id: uuid.UUID,  identifier: uuid.UUID | str) -> None:
        """"""
        entry = await self.get_one_content_entry(tenant_id, identifier)

        try:
            log.info(
                "content.entry.deleted",
                tenant_id=tenant_id,
                content_entry_id=str(identifier)
            )
            await self.repo.delete(entry)
        except DatabaseError as e:
            log.error(
                "content.entry.error",
                tenant_id=tenant_id,
                content_entry_id=str(identifier),
                error=str(e)
            )
            raise BaseAppException(f"{e}")





