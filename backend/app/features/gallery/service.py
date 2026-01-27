import io
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from PIL import Image as PILImage
import uuid


from app.infrastructure.database import IntegrityConstraintError, DatabaseError
from app.infrastructure.clients.supabase_storage import SupabaseStorageClient
from app.shared.errors import BaseAppException, ConflictError, BadRequestError, NotFoundError
from app.infrastructure.observability import log
from app.shared.utils.image_validation import validate_image_file
from .repository import AlbumRepository, ImageRepository
from .schemas import AlbumCreate, AlbumUpdate, AlbumResponse, ImageResponse 
from .models import Album

class AlbumService:
    """
    Album management service handling CRUD operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AlbumRepository(session)

    # === Read Operation ===

    async def get_user_albums(self, user_id: uuid.UUID) -> List[AlbumResponse]:
        """
        Retrieve all albums belonging to a specific user.

        Args:
            user_id: UUID of the user whose albums to retrieve.

        Returns:
            A list of AlbumResponse objects belonging to the user.
            Returns an empty list if no albums exist.
        """
        log.info("album.fetch.all", user_id=user_id)
        return await self.repo.get_all_album_with_images(user_id=user_id)

    async def get_album(self, user_id: uuid.UUID, album_id: uuid.UUID) -> AlbumResponse:
        """
        Retrieve a single album by ID with ownership verification.

        Args:
            user_id: UUID of the user requesting the album.
            album_id: UUID of the album to retrieve.

        Returns:
            The AlbumResponse object matching the provided album_id.

        Raises:
            NotFoundError: If the album does not exist or does not belong to the user.
        """
        album = await self.repo.get_album_with_images(user_id, album_id)

        if not album:
            raise NotFoundError("Album not found")

        log.info("album.get.album", user_id=user_id, album_id=album_id)
        return album    

        
    # === Write Operation ===

    async def create_album(self, user_id: uuid.UUID, data: AlbumCreate) -> Album:
        """
        Create a new album for a user with auto-generated unique slug.

        Args:
            user_id: UUID of the user creating the album.
            data: AlbumCreate schema containing album title and details.

        Returns:
            The newly created AlbumResponse object with generated slug.

        Raises:
            ConflictError: If the album violates database integrity constraints.
            BaseAppException: If a database error occurs during creation.
        """
        log.info(f"User: {user_id} is adding album '{data.title}'")
        try:
            slug = await self.repo.generate_unique_slug(data.title)
            album = await self.repo.create(user_id=user_id, slug=slug, **data.model_dump())

            log.info(
                "album.create",
                user_id=user_id, 
                title=data.title
            )
            
            return AlbumResponse(
            id=album.id,
            title=album.title,
            slug=album.slug,
            cover_url=album.cover_url,
            is_published=album.is_published,
            images=[]  
        )
             
        except IntegrityConstraintError as e:
            log.warning(
                "album.create.integrity_error",
                user_id=str(user_id),
                album_title=data.title,
                error=str(e)
            )
            raise ConflictError("Creates violates constraints")
        except DatabaseError as e:
            log.error(
                "album.database.error",
                user_id=str(user_id),
                error=str(e),
            )
            raise BaseAppException("Failed to create album")
            
    async def update_album(
        self, 
        user_id: uuid.UUID, 
        album_id: uuid.UUID, 
        data: AlbumUpdate
    ) -> Album:
        """
        Partially update an existing album with ownership verification.

        Args:
            user_id: UUID of the user requesting the update.
            album_id: UUID of the album to update.
            data: AlbumUpdate schema containing fields to update.

        Returns:
            The updated Album object with applied changes.

        Raises:
            NotFoundError: If the album does not exist or does not belong to the user.
            ConflictError: If the update violates database integrity constraints.
            BaseAppException: If a database error occurs during update.
        """
        log.info(f"User: {user_id} is updating album '{data.title}'")

        album = await self.get_album(user_id=user_id, album_id=album_id)

        try:
            updated_data = data.model_dump(exclude_unset=True)
            log.info(
                "album.update",
                user_id=user_id,
                album_id=album_id,
                updated_fields = list(updated_data.keys())
            )
            return await self.repo.update(album, **updated_data)
        
        except IntegrityConstraintError as e:
            log.warning(
                "album.update.integrity_error",
                user_id=str(user_id),
                album_title=data.title,
                error=str(e)
            )
            raise ConflictError("Update violates constraints")
        except DatabaseError as e:
            log.error(
                "album.database.error",
                user_id=str(user_id),
                error=str(e),
            )
            raise BaseAppException("Failed to update album")
    
    # TODO Need softdelete!!
    async def delete_album(self, user_id: uuid.UUID, album_id: uuid.UUID) -> None:
        """
        Permanently delete an album after verifying ownership.

        Args:
            user_id: UUID of the user requesting the deletion.
            album_id: UUID of the album to delete.

        Returns:
            None. The album is permanently removed from the database.

        Raises:
            NotFoundError: If the album does not exist or does not belong to the user.
            BaseAppException: If a database error occurs during deletion.
        """
        album = await self.get_album(user_id=user_id, album_id=album_id)
        log.info(f"User: {user_id} is deleting album '{album.title}'")

        try:
            log.info(
                "album.deleted",
                user_id=str(user_id),
                album_id=str(album_id),
                title=album.title,
            )
            await self.repo.delete(album)
        except DatabaseError as e:
            log.error(
                "album.database.error",
                user_id=str(user_id),
                album_id=str(album_id),
                error=str(e)
            )
            raise BaseAppException("Failed to delete album")


class ImageService:
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ImageRepository(session)
        self.album_repo = AlbumRepository(session)
        self.storage = SupabaseStorageClient()

    async def upload_images(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID,
        files: List[UploadFile]
    ) -> List[ImageResponse]:
        """
        Upload multiple images to Supabase Storage and create database records.

        Args:
            user_id: UUID of the authenticated user.
            files: List of UploadFile objects from FastAPI.
            metadata: List of ImageCreate schemas with caption and is_published.

        Returns:
            List of ImageResponse with full image details including URLs.

        Raises:
            BadRequestError: If file count doesn't match metadata, or validation fails.
            ConflictError: If database constraint is violated.
            BaseAppException: For storage or database failures.
        """

        log.info(
            "gallery.upload.started",
            user_id=str(user_id),
            file_count=len(files)
        )

        album = await self.album_repo.get_by_user_and_id(user_id, album_id)
        if not album:
          raise NotFoundError("Album not found")

        uploaded_images: List[ImageResponse] = []

        for i, file in enumerate(files):
            image_response = await self._process_single_image(
                user_id,
                album_id=album_id,
                album_title=album.title,
                file=file
            )
            uploaded_images.append(image_response)

            if i == 0 and not album.cover_url:
                await self.album_repo.update(album, cover_url=image_response.image_url)

        log.info(
            "gallery.upload.completed",
            user_id=str(user_id),
            success_count=len(uploaded_images)
        )

        return uploaded_images

    async def _process_single_image(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID,
        album_title: str, 
        file: UploadFile,
    ) -> ImageResponse:
        """
        Process a single image: validate, upload, extract dimensions, save to DB.

        Args:
            user_id: UUID of the authenticated user.
            file: Single UploadFile object.
            meta: ImageCreate schema with caption and is_published.

        Returns:
            ImageResponse with full image details.
        """

        # Validate first!
        contents = await validate_image_file(file)
        # Extract image dimensions
        width, height = self._get_image_dimensions(contents)
        # Generate unique slug
        slug = await self.repo.generate_unique_slug(album_title)

        # Upload to Supabase Storage
        try:
            image_url = await self.storage.upload_image(
                file_bytes=contents,
                user_id=user_id,
                folder="Gallery" ,
                file_name=f"{slug}.{file.content_type.split('/')[-1]}",
                content_type=file.content_type
            )
        except Exception as e:
            log.error(
                "gallery.storage.upload_failed",
                user_id=str(user_id),
                filename=file.filename,
                error=str(e)
            )
            raise BaseAppException(f"Failed to upload image to storage: {str(e)}")

        # 6. Create database record
        try:
            db_image = await self.repo.create(
                user_id=user_id,
                album_id=album_id,
                slug=slug,
                width=width,
                height=height,
                image_url=image_url,
            )

            log.info(
                "gallery.image.created",
                user_id=str(user_id),
                image_id=str(db_image.id),
                slug=slug
            )

            return ImageResponse.model_validate(db_image)

        except IntegrityConstraintError as e:
            log.warning(
                "gallery.create.integrity_error",
                user_id=str(user_id),
                album_title=album_title,
                error=str(e)
            )
            raise ConflictError("Image creation violates database constraints")
        except DatabaseError as e:
            log.error(
                "gallery.database.error",
                user_id=str(user_id),
                error=str(e)
            )
            raise BaseAppException("Failed to save image to database")

    # Read Operations

    async def get_user_images(
        self,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ImageResponse]:
        """
        Get all images for a specific user with pagination.

        Args:
            user_id: UUID of the user.
            limit: Maximum number of images to return.
            offset: Number of images to skip.

        Returns:
            List of ImageResponse objects.
        """
        images = await self.repo.get_all_by_user_id(user_id=user_id, limit=limit, offset=offset)
        return [
            ImageResponse.model_validate(img)
            for img in images
        ]
    
    async def get_image_by_slug(self, user_id: uuid.UUID, slug: str) -> ImageResponse:
        """
        Get a single image by its slug.

        Args:
            user_id: UUID of the user.  
            slug: Unique slug identifier.

        Returns:
            ImageResponse object.

        Raises:
            NotFoundError: If image with slug doesn't exist.
        """
        
        image =  await self.repo.get_by_slug(slug=slug, user_id=user_id)
        if not image:
            raise NotFoundError("Image not found")
        
        return ImageResponse.model_validate(image)

    # === Public Access (no auth required) ===

    async def get_public_images(self, user_id: uuid.UUID, limit: int = 100, offset: int = 0):
        """Get all images from published albums for landing page"""
        log.info("gallery.public.fetch.all", user_id=user_id)
        images = await self.repo.get_public_images(user_id, limit, offset)
        return [ImageResponse.model_validate(img) for img in images]

    async def get_public_image_by_slug(self, user_id: uuid.UUID, slug: str):
        """Get a single image by slug if its album is published"""
        image = await self.repo.get_public_image_by_slug(user_id, slug)
        if not image:
            raise NotFoundError("Image not found")
        log.info("gallery.public.fetch", user_id=user_id, slug=slug)
        return ImageResponse.model_validate(image)

    # === Helpers ===


    def _get_image_dimensions(self, file_bytes: bytes) -> tuple[int, int]:
        try:
            image = PILImage.open(io.BytesIO(file_bytes))
            return image.size
        except (IOError, OSError) as e:
            log.error("gallery.image.dimensions_failed", error=str(e))
            raise BadRequestError("Could not process image. File may be corrupted.")

