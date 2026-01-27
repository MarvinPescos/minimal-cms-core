from fastapi import UploadFile
from app.shared.errors import BadRequestError

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

async def validate_image_file(file: UploadFile) -> bytes:
    """
    Validate image file content type and size.
    
    Args:
        file: The uploaded file to validate
        
    Returns:
        bytes: The file contents if validation passes
        
    Raises:
        BadRequestError: If file type or size is invalid
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestError(
            f"Invalid content type: {file.content_type}",
            f"Allowed types: {ALLOWED_IMAGE_TYPES}"
        )
    
    contents = await file.read()
    
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise BadRequestError(
            f"File '{file.filename}' exceeds maximum size of 5MB"
        )
    
    return contents