from typing import List
from httpx import delete
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.infrastructure.database import IntegrityConstraintError, DatabaseError
from app.shared.errors import BaseAppException, ConflictError, BadRequestError, NotFoundError
from app.infrastructure.observability import log

from .models import ContentEntry, ContentType
from .repository import ContentEntryRepository, ContentTypeRepository
from .schemas import ContentEntryResponse, ContentTypeCreate, ContentTypeUpdate, ContentTypeResponse

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

