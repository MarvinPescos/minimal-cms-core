from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid

# === Reusable validators ===

# Images

# class ImageCreate(BaseModel):
#     """Schema with shared image fields"""
#     caption: str = Field(min_length=3, max_length=150)
#     is_published: bool = Field(default=False, description="Allows drafting")


# # Not been use yet
# class ImageUpdate(BaseModel):
#     """Schema for updating image metadata (caption, publish status)"""
#     caption: Optional[str] = Field(None, min_length=3, max_length=150, description="New caption for the image")
#     is_published: Optional[bool] = Field(None, description="Update publish status")


class ImageResponse(BaseModel):
    """Schema for returning image details"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="UUID of the image")
    slug: str = Field(..., description="Unique slug for the image")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    image_url: str = Field(..., description="Public URL of the uploaded image")


# Album

class AlbumCreate(BaseModel):
    """Schema for creating Album"""
    title: str = Field(min_length=3, max_length=150)
    # cover_url: str = Field(..., description="Cover image URL")
    is_published: bool = Field(default=False, description="Allows drafting")

class AlbumUpdate(BaseModel):
    """Schema for updating Album"""
    title: str | None = Field(None, min_length=3, max_length=150, description="New caption for the Album")
    is_published: bool | None = Field(None, description="Update publish status")

class AlbumResponse(BaseModel):
    """Schema for getting an album + the images"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    slug: str
    cover_url: str | None = None
    is_published: bool
    images: List[ImageResponse] = []






