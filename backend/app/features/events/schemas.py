from time import timezone
from pydantic import BaseModel, Field, AfterValidator
from typing import Annotated
from datetime import datetime, timezone
import uuid

# === Reusable validators ===

def validate_datetime(v: datetime) -> datetime:
    """Date & time cannot be in the past"""
    if v < datetime.now(timezone.utc):
        raise ValueError("Date & time cannot be in the past")
    return v

ValidatedDatetime = Annotated[datetime | None, AfterValidator(validate_datetime)]

# === Schemas ===

class EventBase(BaseModel):
    """Base schema with shared event fields"""
    title: str = Field(min_length=3, max_length=150, description="Title of the said event")
    summary: str = Field(min_length=3, max_length=255, description="Short descriptive summary of the event")
    content: str = Field(min_length=3, description="Full content of the event")
    # cover_image: str = Field(..., description="Url of the cover image")
    start_at: datetime = Field(..., description="date & time of the event (start_at)")
    end_at: datetime = Field(..., description="date & time of the event (end_at)")
    location: str = Field(..., description="Location of the event eg. Main Hall, Central Park")
    location_url: str = Field(..., description="A direct link to Google Maps for off-site events")
    is_published: bool = Field(..., description="Allows drafting")


class EventCreate(EventBase):
    """Schema for creating an event"""
    start_at: ValidatedDatetime = Field(..., description="date & time of the event (start_at)")
    end_at: ValidatedDatetime = Field(..., description="date & time of the event (end_at)")


class EventUpdate(BaseModel):
    """Schema for updating an event - all fields optional"""
    title: str | None = Field(None, min_length=3, max_length=150)
    summary: str | None = Field(None, min_length=3, max_length=255)
    content: str | None = Field(None, min_length=3)
    # cover_image: str | None = None
    start_at: ValidatedDatetime = None
    end_at: ValidatedDatetime = None
    location: str | None = None
    location_url: str | None = None
    is_published: bool | None = None


class EventResponse(EventBase):
    """Schema for returning an event"""
    id: uuid.UUID = Field(..., description="UUID of the event")
    slug: str = Field(..., description="Slug of tyhe given event")
    cover_image: str | None = Field(None, description="Url of the cover image")

