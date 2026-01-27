from fastapi import APIRouter, Depends, status, Request, File, UploadFile, Form
from typing import List
import uuid

from app.infrastructure.security import require_auth, AuthenticatedUser
from app.infrastructure.cache import limiter, RateLimits
from .schemas import (
    EventResponse,
    EventCreate,
    EventUpdate
)
from .service import EventService
from .dependencies import get_event_service

router = APIRouter(prefix="/events", tags=["Events"])


# === Read Operations ===

# Public endpoint 
@router.get(
    "/public",
    response_model=List[EventResponse],
    status_code=status.HTTP_200_OK,
    summary="List public events",
    description="""
    Retrieve all published events for a specific tenant's landing page.
    
    - **No Authentication Required**: This is a public endpoint.
    - **Filtering**: Only published events are returned.
    - **Pagination**: Use limit and offset for pagination.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "List of published events retrieved successfully"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def list_public_events(
    request: Request,
    user_id: uuid.UUID,  
    limit: int = 50,
    offset: int = 0,
    service: EventService = Depends(get_event_service)
):
    """Get all published events for a specific tenant's landing page."""
    return await service.get_public_events(user_id, limit, offset)


@router.get(
    "/public/{slug}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public event by slug",
    description="""
    Retrieve a single published event by its SEO-friendly slug.
    
    - **No Authentication Required**: This is a public endpoint.
    - **SEO-Friendly**: Uses slug instead of UUID for cleaner URLs.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "Event details retrieved successfully"},
        404: {"description": "Event not found or not published"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_public_event(
    request: Request,
    slug: str,
    user_id: uuid.UUID, 
    service: EventService = Depends(get_event_service)
):
    """Get a single published event by slug for a specific tenant's landing page."""
    return await service.get_public_event_by_slug(user_id, slug)


@router.get(
    "/",
    response_model=List[EventResponse],
    status_code=status.HTTP_200_OK,
    summary="List all events",
    description="""
    Retrieve all events belonging to the authenticated user.
    
    - **Ordering**: Events are returned by start date (soonest first).
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "List of events retrieved successfully"},
        401: {"description": "User is not authenticated"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def list_events(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: EventService = Depends(get_event_service)
):
    """Get all events for the current user."""
    return await service.get_user_events(uuid.UUID(current_user.user_id))


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get event details",
    description="""
    Retrieve details of a specific event by its ID.
    
    - **Authorization**: User can only access their own events.
    - **Rate Limit**: 200 requests per minute.
    """,
    responses={
        200: {"description": "Event details retrieved successfully"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Event not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.READ_HEAVY)
async def get_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: EventService = Depends(get_event_service)
):
    """Get a specific event by ID."""
    return await service.get_event(uuid.UUID(current_user.user_id), event_id)


# === Write Operations ===

@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
    description="""
    Create a new event for the authenticated user.
    
    - **Title**: Must be 3-150 characters.
    - **Dates**: start_at and end_at cannot be in the past.
    - **Draft Mode**: Set is_published to false to save as draft.
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        201: {"description": "Event created successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "User is not authenticated"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def create_event(
    request: Request,
    data: str = Form(..., description="Event data as JSON string"),
    file: UploadFile | None = File(None, description="Image files to upload (max 5MB each)"),
    current_user: AuthenticatedUser = Depends(require_auth),
    service: EventService = Depends(get_event_service)
):
    """Create a new event."""
    event_data = EventCreate.model_validate_json(data)
    if file:
        return await service.add_event(uuid.UUID(current_user.user_id), file, event_data)
    else:
        return await service.add_event(uuid.UUID(current_user.user_id), None, event_data)


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an event",
    description="""
    Update an existing event. Only provided fields will be updated.
    
    - **Partial Update**: Only include fields you want to change.
    - **Authorization**: User can only update their own events.
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        200: {"description": "Event updated successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Event not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def update_event(
    request: Request,
    event_id: uuid.UUID,
    data: EventUpdate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: EventService = Depends(get_event_service)
):
    """Update an existing event."""
    return await service.update_event(uuid.UUID(current_user.user_id), event_id, data)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
    description="""
    Permanently delete an event by its ID.
    
    - **Authorization**: User can only delete their own events.
    - **Warning**: This action cannot be undone.
    - **Rate Limit**: 100 requests per minute.
    """,
    responses={
        204: {"description": "Event deleted successfully"},
        401: {"description": "User is not authenticated"},
        404: {"description": "Event not found"},
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit(RateLimits.STANDARD)
async def delete_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: EventService = Depends(get_event_service)
):
    """Delete an event."""
    await service.delete_event(uuid.UUID(current_user.user_id), event_id)
    return None
