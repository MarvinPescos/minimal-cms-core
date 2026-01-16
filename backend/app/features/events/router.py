from fastapi import APIRouter, Depends, status
from typing import List
import uuid

from app.infrastructure.security import require_auth, AuthenticatedUser
from .schemas import (
    EventResponse,
    EventCreate,
    EventUpdate
)
from .service import EventService
from .dependencies import get_event_service

router = APIRouter(prefix="/events", tags=["Events"])


# === Read Operations ===

@router.get(
    "/",
    response_model=List[EventResponse],
    status_code=status.HTTP_200_OK,
    summary="List all events",
    description="""
    Retrieve all events belonging to the authenticated user.
    
    - **Ordering**: Events are returned by start date (soonest first).
    - **Rate Limit**: This endpoint is "Read Heavy" and restricted to prevent abuse.
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
# @limiter.limit(RateLimits.READ_HEAVY)  # TODO: Add rate limiting
async def list_events(
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
    - **Rate Limit**: Restricted to prevent abuse.
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
# @limiter.limit(RateLimits.READ)  # TODO: Add rate limiting
async def get_event(
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
    - **Rate Limit**: Restricted to prevent spam.
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
# @limiter.limit(RateLimits.WRITE)  # TODO: Add rate limiting
async def create_event(
    data: EventCreate,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: EventService = Depends(get_event_service)
):
    """Create a new event."""
    return await service.add_event(uuid.UUID(current_user.user_id), data)


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an event",
    description="""
    Update an existing event. Only provided fields will be updated.
    
    - **Partial Update**: Only include fields you want to change.
    - **Authorization**: User can only update their own events.
    - **Rate Limit**: Restricted to prevent abuse.
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
# @limiter.limit(RateLimits.WRITE)  # TODO: Add rate limiting
async def update_event(
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
    - **Rate Limit**: Restricted to prevent abuse.
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
# @limiter.limit(RateLimits.WRITE)  # TODO: Add rate limiting
async def delete_event(
    event_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_auth),
    service: EventService = Depends(get_event_service)
):
    """Delete an event."""
    await service.delete_event(uuid.UUID(current_user.user_id), event_id)
    return None
