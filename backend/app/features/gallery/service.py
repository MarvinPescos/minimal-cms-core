import io
from typing import List
from fastapi import UploadFile
from PIL import Image as PILImage
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession

import uuid

from app.infrastructure.database import IntegrityConstraintError, DatabaseError
from app.infrastructure.clients.supabase_storage import SupabaseStorageClient
from app.shared.errors import BaseAppException, ConflictError, BadRequestError, NotFoundError
from app.infrastructure.observability import log
from app.shared.utils.image_validation import validate_image_file
from .repository import AlbumRepository, ImageRepository
from .schemas import AlbumCreate, AlbumUpdate, AlbumResponse, ImageResponse 
from .models import Album, Image

class AlbumService:
    """
    Album management service handling CRUD operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AlbumRepository(session)

    # === Read Operation ===

    async def get_tenant_albums(
        self,
        tenant_id: uuid.UUID, 
        is_published: bool | None = None
    ) -> List[Album]:
        """
        List all albums for a given tenant.

        Args:
            tenant_id: Tenant to scope the query to.
            is_published: Optional filter for publication status.

        Returns:
            List of `Album` records belonging to the tenant.
        """
        log.info("album.fetch.all", tenant_id=tenant_id)
        return await self.repo.get_all_albums(tenant_id, is_published)

    async def get_album(self, tenant_id: uuid.UUID, identifier: str | uuid.UUID) -> Album:
        """
        Fetch a single album by ID or slug within a tenant.

        Args:
            tenant_id: Tenant to scope the query to.
            identifier: UUID or slug identifying the album.

        Returns:
            The matching `Album`.

        Raises:
            NotFoundError: If the album does not exist in the tenant.
        """
        album = await self.repo.get_one(tenant_id=tenant_id, identifier=identifier)

        if not album:
            raise NotFoundError("Album not found")

        log.info("album.get.album", tenant_id=tenant_id, identifier=identifier)

        return album    

        
    # === Write Operation ===

    async def create_album(self, tenant_id: uuid.UUID, data: AlbumCreate) -> AlbumResponse:
        """
        Create a new tenant-scoped album.

        Args:
            tenant_id: Tenant that owns the album.
            data: Payload containing the album definition.

        Returns:
            The created `AlbumResponse`.

        Raises:
            ConflictError: If constraints (e.g., uniqueness) are violated.
            BaseAppException: For unexpected database errors.
        """
        try:
            slug = await self.repo.generate_unique_slug(data.title, Album.tenant_id == tenant_id)
            album = await self.repo.create(tenant_id=tenant_id, slug=slug, **data.model_dump())

            log.info(
                "album.create",
                tenant_id=tenant_id, 
                title=data.title
            )
            
            return AlbumResponse(
            id=album.id,
            title=album.title,
            slug=album.slug,
            cover_url=album.cover_url,
            is_published=album.is_published,
        )
             
        except IntegrityConstraintError as e:
            log.warning(
                "album.create.integrity_error",
                user_id=str(tenant_id),
                album_title=data.title,
                error=str(e)
            )
            raise ConflictError("Creates violates constraints")
        except DatabaseError as e:
            log.error(
                "album.database.error",
                user_id=str(tenant_id),
                error=str(e),
            )
            raise BaseAppException("Failed to create album")
            
    async def update_album(
        self, 
        tenant_id: uuid.UUID, 
        identifier: str | uuid.UUID, 
        data: AlbumUpdate
    ) -> Album:
        """
        Partially update an existing album.

        Args:
            tenant_id: Tenant to scope the query to.
            identifier: UUID or slug identifying the album.
            data: Partial update payload.

        Returns:
            The updated `Album`.

        Raises:
            NotFoundError: If the album does not exist.
            ConflictError: If constraints are violated.
            BaseAppException: For unexpected database errors.
        """
        album = await self.get_album(tenant_id=tenant_id, identifier=identifier)

        try:
            updated_data = data.model_dump(exclude_unset=True)
            log.info(
                "album.update",
                tenant_id=tenant_id,
                identifier=identifier,
                updated_fields = list(updated_data.keys())
            )
            return await self.repo.update(album, **updated_data)
        
        except IntegrityConstraintError as e:
            log.warning(
                "album.update.integrity_error",
                tenant_id=str(tenant_id),
                album_title=data.title,
                error=str(e)
            )
            raise ConflictError("Update violates constraints")
        except DatabaseError as e:
            log.error(
                "album.database.error",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            raise BaseAppException("Failed to update album")
    
    # TODO Need softdelete!!
    async def delete_album(self, tenant_id: uuid.UUID, identifier: str | uuid.UUID) -> None:
        """
        Permanently delete a tenant-scoped album.

        Args:
            tenant_id: Tenant to scope the query to.
            identifier: UUID or slug identifying the album.

        Raises:
            NotFoundError: If the album does not exist.
            BaseAppException: For unexpected database errors.
        """
        album = await self.get_album(tenant_id=tenant_id, identifier=identifier)

        try:
            log.info(
                "album.deleted",
                tenant_id=str(tenant_id),
                identifier=str(identifier),
                title=album.title,
            )
            await self.repo.delete(album)
        except DatabaseError as e:
            log.error(
                "album.database.error",
                tenant_id=str(tenant_id),
                identifier=str(identifier),
                error=str(e)
            )
            raise BaseAppException("Failed to delete album")


# ===============================================================


class ImageService:
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ImageRepository(session)
        self.album_repo = AlbumRepository(session)
        self.storage = SupabaseStorageClient()

    async def upload_images(
        self,
        tenant_id: uuid.UUID,   
        album_identifier: str,
        files: List[UploadFile]
    ) -> List[ImageResponse]:
        """
        Upload multiple images to storage and create database records.

        Args:
            tenant_id: Tenant owning the album.
            album_identifier: UUID or slug of the target album.
            files: List of uploaded files.

        Returns:
            List of `ImageResponse` objects.

        Raises:
            NotFoundError: If the album does not exist.
            BaseAppException: If storage upload or database save fails.
        """
        log.info(
            "gallery.upload.started",
            tenant_id=str(tenant_id),
            file_count=len(files)
        )

        album = await self.album_repo.get_one(tenant_id=tenant_id, identifier=album_identifier)
        if not album:
            raise NotFoundError("Album not found")

        uploaded_images: List[ImageResponse] = []

        for i, file in enumerate(files):
            image_response = await self._process_single_image(
                tenant_id=tenant_id,
                album_id=album.id,
                album_title=album.title,
                file=file
            )
            uploaded_images.append(image_response)

            if i == 0 and not album.cover_url:
                await self.album_repo.update(album, cover_url=image_response.image_url)

        log.info(
            "gallery.upload.completed",
            tenant_id=str(tenant_id),
            success_count=len(uploaded_images)
        )

        return uploaded_images

    # === Read Operations ===

    async def get_images_in_album(
        self,
        tenant_id: uuid.UUID,
        album_identifier: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ImageResponse]:
        """
        List all images within a specific album for a tenant.

        Args:
            tenant_id: Tenant to scope the query to.
            album_identifier: UUID or slug of the album.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of `ImageResponse` objects.
        """
        images = await self.repo.get_by_album(
            tenant_id=tenant_id,
            album_identifier=album_identifier,
            limit=limit,
            offset=offset
        )
        log.info("gallery.get.images", tenant_id=tenant_id)
        return [ImageResponse.model_validate(img) for img in images]



    async def get_public_images(
        self,
        tenant_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ImageResponse]:
        """
        List all images from published albums for public viewing.

        Args:
            tenant_id: Tenant to scope the query to.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of `ImageResponse` objects.
        """
        images = await self.repo.get_public_images(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset
        )
        log.info("gallery.public.get.images", tenant_id=tenant_id)
        return [ImageResponse.model_validate(img) for img in images]


    # Helper for delete function. Might add it as endpoint.
    async def get_image(self, tenant_id: uuid.UUID, image_id: uuid.UUID) -> Image:
        """
        Fetch a single image by ID within a tenant.

        Args:
            tenant_id: Tenant to scope the query to.
            image_id: UUID of the image.

        Returns:
            The matching `Image`.

        Raises:
            NotFoundError: If the image does not exist.
        """
        image = await self.repo.get_scoped_by_id(tenant_id=tenant_id, image_id=image_id)
        if not image:
            raise NotFoundError("Image not found")
        return image

    # === Write Operations ===

    async def delete_image(self, tenant_id: uuid.UUID, image_id: uuid.UUID) -> None:
        """
        Permanently delete an image from storage and database.

        Args:
            tenant_id: Tenant owning the image.
            image_id: UUID of the image to delete.

        Raises:
            NotFoundError: If the image does not exist.
            BaseAppException: If storage deletion or database operation fails.
        """
        image = await self.get_image(tenant_id, image_id)

        try:
            log.info("image.deleted", tenant_id=str(tenant_id), image_id=str(image_id))

            path = urlparse(image.image_url).path
            file_name_with_extension = path.rsplit("/", 1)[-1]

            await self.storage.delete_image(
                folder="Gallery",
                file_name=file_name_with_extension,
                tenant_id=tenant_id
            )
            await self.repo.delete(image)
        except DatabaseError as e:
            log.error(
                "image.database.error",
                tenant_id=str(tenant_id),
                image_id=str(image_id),
                error=str(e)
            )
            raise BaseAppException("Failed to delete image")

    # === Helpers ===

    def _get_image_dimensions(self, file_bytes: bytes) -> tuple[int, int]:
        try:
            image = PILImage.open(io.BytesIO(file_bytes))
            return image.size
        except (IOError, OSError) as e:
            log.error("gallery.image.dimensions_failed", error=str(e))
            raise BadRequestError("Could not process image. File may be corrupted.")

    async def _process_single_image(
        self,
        tenant_id: uuid.UUID,
        album_id: uuid.UUID,
        album_title: str,
        file: UploadFile,
    ) -> ImageResponse:
        """Validate, upload, and save a single image."""
        contents = await validate_image_file(file)
        width, height = self._get_image_dimensions(contents)
        slug = await self.repo.generate_unique_slug(album_title, Image.album_id == album_id)

        try:
            image_url = await self.storage.upload_image(
                file_bytes=contents,
                tenant_id=tenant_id,
                folder="Gallery",
                file_name=f"{slug}.{file.content_type.split('/')[-1]}",
                content_type=file.content_type
            )
        except Exception as e:
            log.error(
                "gallery.storage.upload_failed",
                tenant_id=str(tenant_id),
                filename=file.filename,
                error=str(e)
            )
            raise BaseAppException(f"Failed to upload image to storage: {str(e)}")

        try:
            db_image = await self.repo.create(
                album_id=album_id,
                slug=slug,
                width=width,
                height=height,
                image_url=image_url,
            )
            log.info(
                "gallery.image.created",
                tenant_id=str(tenant_id),
                image_id=str(db_image.id),
                slug=slug
            )
            return ImageResponse.model_validate(db_image)

        except IntegrityConstraintError as e:
            log.warning(
                "gallery.create.integrity_error",
                tenant_id=str(tenant_id),
                album_title=album_title,
                error=str(e)
            )
            raise ConflictError("Image creation violates database constraints")
        except DatabaseError as e:
            log.error("gallery.database.error", tenant_id=str(tenant_id), error=str(e))
            raise BaseAppException("Failed to save image to database")

