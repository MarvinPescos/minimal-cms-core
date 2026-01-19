import pytest
from httpx import AsyncClient

@pytest.fixture
async def created_fridge_item(client, mock_user_token):
    """Helper Fixture to create an item"""
    response = await client.post("/events", json={
            {
                "title": "Future Tech Summit 2026",
                "summary": "Join us for an immersive day exploring the latest advancements in AI and cloud computing.",
                "content": "<p>The Future Tech Summit brings together industry leaders, developers, and innovators. <strong>Agenda includes:</strong> Keynote speeches, hands-on workshops, and networking opportunities. Lunch will be provided.</p>",
                "cover_image": "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1000&q=80",
                "start_at": "2026-02-20T09:00:00Z",
                "end_at": "2026-02-20T17:00:00Z",
                "location": "Grand Convention Center, Hall A",
                "location_url": "https://maps.google.com/?q=Grand+Convention+Center",
                "is_published": true,
                "id": "4c55da2b-9497-4566-99eb-587707a66298"
             }
    })
    assert response.status_code == 201
    return response.json()