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
    """
    Service responsible for tenant-scoped *content type* management.

    A content type defines the JSON schema used to validate content entry payloads.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContentTypeRepository(session)
    

    async def get_all_content_type(self, tenant_id: uuid.UUID) -> List[ContentType]:
        """
        List all content types for a given tenant.

        Args:
            tenant_id: Tenant to scope the query to.

        Returns:
            List of `ContentType` records belonging to the tenant.
        """
        log.info("content.type.get.all", tenant_id=tenant_id)
        return await self.repo.get_many(tenant_id)

    async def get_content_type(self, tenant_id:uuid.UUID, content_type_id: uuid.UUID) -> ContentType:
        """
        Fetch a single content type by ID within a tenant.

        Args:
            tenant_id: Tenant to scope the query to.
            content_type_id: Content type UUID.

        Returns:
            The matching `ContentType`.

        Raises:
            NotFoundError: If the content type does not exist in the tenant.
        """
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
        """
        Create a new tenant-scoped content type.

        Args:
            tenant_id: Tenant that owns the content type.
            data: Payload containing the content type definition.

        Returns:
            The created `ContentType`.

        Raises:
            ConflictError: If constraints (e.g., uniqueness) are violated.
            BaseAppException: For unexpected database errors.
        """
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
        """
        Partially update an existing content type.

        Args:
            tenant_id: Tenant to scope the query to.
            content_type_id: UUID of the content type to update.
            data: Partial update payload.

        Returns:
            The updated `ContentType`.

        Raises:
            NotFoundError: If the content type does not exist.
            ConflictError: If constraints are violated.
            BaseAppException: For unexpected database errors.
        """
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
        """
        Permanently delete a tenant-scoped content type.

        Args:
            tenant_id: Tenant to scope the query to.
            content_type_id: UUID of the content type to delete.

        Raises:
            NotFoundError: If the content type does not exist.
            BaseAppException: For unexpected database errors.
        """
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
        """
        List content entries for a tenant, optionally scoped to a specific content type.

        Args:
            tenant_id: Tenant to scope the query to.
            content_type_id: Optional UUID of a content type to filter by.

        Returns:
            List of `ContentEntry` records.
        """
        log.info("content.entry.get.all", tenant_id=tenant_id, content_type_id=content_type_id)
        return await self.repo.get_all_content_entry(tenant_id, content_type_id)

    async def get_one_content_entry(self, tenant_id: uuid.UUID, identifier: uuid.UUID | str) -> ContentEntry:
        """
        Fetch a single content entry by UUID or slug within a tenant.

        Args:
            tenant_id: Tenant to scope the query to.
            identifier: UUID (direct ID) or string (slug).

        Returns:
            The matching `ContentEntry`.

        Raises:
            NotFoundError: If the entry does not exist in the tenant.
        """
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
        """
        Create a new content entry for a tenant.

        The entry payload is validated against the JSON schema defined by the selected content type.

        Args:
            tenant_id: Tenant that owns the entry.
            content_type_identifier: UUID or slug identifying the content type.
            data: Entry creation payload (typed fields + title + `data` JSON object).
            user_id: UUID string of the user creating the entry (stored as `created_by`).

        Returns:
            The created `ContentEntry`.

        Raises:
            NotFoundError: If the referenced content type does not exist.
            BadRequestError: If the payload does not validate against the content type schema.
            ConflictError: If database constraints are violated (e.g., uniqueness).
            BaseAppException: For unexpected database errors.
        """
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
        """
        Partially update an existing content entry.

        If the update includes a new `data` payload, it is validated against the content type JSON schema.

        Args:
            tenant_id: Tenant to scope the query to.
            identifier: UUID or slug identifying the entry.
            data: Partial update payload.
            user_id: UUID string of the user performing the update (stored as `updated_by`).

        Returns:
            The updated `ContentEntry`.

        Raises:
            NotFoundError: If the entry does not exist.
            BadRequestError: If the updated JSON payload fails schema validation.
            ConflictError: If database constraints are violated.
            BaseAppException: For unexpected database errors.
        """
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
        """
        Permanently delete a content entry within a tenant.

        Args:
            tenant_id: Tenant to scope the query to.
            identifier: UUID or slug identifying the entry.

        Raises:
            NotFoundError: If the entry does not exist.
            BaseAppException: For unexpected database errors.
        """
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





