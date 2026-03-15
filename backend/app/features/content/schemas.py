from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Any
import uuid

class ContentTypeCreate(BaseModel):
    name: str = Field(
        min_length=3, 
        max_lenght=150, 
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Machine name: lowercase, underscores only (e.g. menu_item)",
    )
    label: str = Field(
        min_length=2,
        max_length=150,
        description="Human-friendly name (e.g. Menu Items)",
    )
    description: str | None = Field(
        None, 
        max_length=500,
        description="Help text for the admin panel"
    )
    json_schema: dict = Field(
        ...,
        description="JSON Schema that defines the structures of entry data"
    )


class ContentTypeUpdate(BaseModel):
    label: str | None = Field(
        None,
        min_length=2,
        max_length=150,
    )
    description: str | None = Field(
        None, 
        max_length=500,
    )
    json_schema: dict | None = None
    is_active: bool | None = None


class ContentTypeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    label: str
    description: str | None
    json_schema: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

# === ContentEntry Schema === 

class ContentEntryBase(BaseModel):
    title: str = Field(min_length=3 ,max_length=255)
    summary: str | None = Field(None, max_length=500)
    data: dict[str, Any] = Field(..., description="Content payload — validated against the content type's json_schema")
    cover_image: str | None = Field(None, max_length=255, description="Cover image of the content could be None")
    is_published: bool = Field(default=False, description="For drafting or publish on the spot")
    sort_order: int = 0


class ContentEntryUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    summary: str | None = Field(None, max_length=500)
    data: dict[str, Any] | None = None
    cover_image: str | None = Field(None, max_length=255)
    is_published: bool | None = None
    sort_order: int | None = None


class ContentEntryResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    content_type_id: uuid.UUID
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None
    slug: str
    title: str
    summary: str | None
    data: dict[str, Any]
    cover_image: str | None
    is_published: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
