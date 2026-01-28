import pytest
import json
from httpx import AsyncClient

@pytest.fixture
async def created_events(client, mock_user_token):
    """Helper Fixture to create an event for tests that need an existing event"""
    event_data = {
        "title": "Future Tech Summit 2026",
        "summary": "Join us for an immersive day exploring the latest advancements in AI and cloud computing.",
        "content": "<p>The Future Tech Summit brings together industry leaders, developers, and innovators.</p>",
        "start_at": "2026-02-20T09:00:00Z",
        "end_at": "2026-02-20T17:00:00Z",
        "location": "Grand Convention Center, Hall A",
        "location_url": "https://maps.google.com/?q=Grand+Convention+Center",
        "is_published": True,
    }
    response = await client.post(
        "/events/",
        data={"data": json.dumps(event_data)}
    )
    assert response.status_code == 201
    return response.json()

@pytest.mark.asyncio
async def test_create_event(client, mock_user_token):
    """Test creating event works"""
    event_data = {
        "title": "Future Tech Summit 2026",
        "summary": "Join us for an immersive day exploring the latest advancements in AI and cloud computing.",
        "content": "<p>The Future Tech Summit brings together industry leaders.</p>",
        "start_at": "2026-02-20T09:00:00Z",
        "end_at": "2026-02-20T17:00:00Z",
        "location": "Grand Convention Center, Hall A",
        "location_url": "https://maps.google.com/?q=Grand+Convention+Center",
        "is_published": True,
    }
    response = await client.post(
        "/events/",
        data={"data": json.dumps(event_data)}  # Form data, not json
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Future Tech Summit 2026"
    assert "id" in data
    assert data["is_published"] is True


@pytest.mark.asyncio
async def test_list_events(client, mock_user_token, created_events):
    """Test listing all events for a user"""
    response = await client.get("/events/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify structure of returned events
    assert "id" in data[0]
    assert "title" in data[0]


@pytest.mark.asyncio
async def test_get_event(client, mock_user_token, created_events):
    """Test getting a single event by ID"""
    event_id = created_events["id"]
    response = await client.get(f"/events/{event_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_id
    assert data["title"] == "Future Tech Summit 2026"


@pytest.mark.asyncio
async def test_get_event_not_found(client, mock_user_token):
    """Test getting a non-existent event returns 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/events/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_event(client, mock_user_token, created_events):
    """Test updating an event"""
    event_id = created_events["id"]
    response = await client.patch(f"/events/{event_id}", json={
        "title": "Updated Tech Summit 2026",
        "summary": "Updated summary for the tech summit.",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Tech Summit 2026"
    assert data["summary"] == "Updated summary for the tech summit."
    # Ensure other fields remain unchanged
    assert data["location"] == "Grand Convention Center, Hall A"


@pytest.mark.asyncio
async def test_update_event_not_found(client, mock_user_token):
    """Test updating a non-existent event returns 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(f"/events/{fake_id}", json={
        "title": "This Should Fail"
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_event(client, mock_user_token):
    """Test deleting an event"""
    # First, create an event to delete
    event_data = {
        "title": "Event To Delete",
        "summary": "This event will be deleted.",
        "content": "<p>Temporary event content.</p>",
        "start_at": "2026-03-15T10:00:00Z",
        "end_at": "2026-03-15T12:00:00Z",
        "location": "Test Location",
        "location_url": "https://maps.google.com/?q=Test+Location",
        "is_published": False,
    }
    create_response = await client.post(
        "/events/",
        data={"data": json.dumps(event_data)}
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["id"]

    # Delete the event
    delete_response = await client.delete(f"/events/{event_id}")
    assert delete_response.status_code == 204

    # Verify it no longer exists
    get_response = await client.get(f"/events/{event_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_not_found(client, mock_user_token):
    """Test deleting a non-existent event returns 404"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/events/{fake_id}")
    assert response.status_code == 404
