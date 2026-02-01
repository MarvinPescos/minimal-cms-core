import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.test.conftest import TEST_USER_ID


# === Public endpoints (no auth) ===


@pytest.fixture
async def published_album_with_image(client, mock_user_token, tiny_png, mock_storage):
    """Create a published album with one image for testing public endpoints."""
    album_response = await client.post(
        "/album/",
        json={"title": "Public Gallery", "is_published": True},
    )
    assert album_response.status_code == 201
    album = album_response.json()
    upload_response = await client.post(
        f"/image/{album['id']}",
        files=[("files", ("test.png", tiny_png, "image/png"))],
    )
    assert upload_response.status_code == 201
    images = upload_response.json()
    return {"album": album, "image": images[0]}


@pytest.mark.asyncio
async def test_list_public_images_empty(client):
    """Test listing public images returns empty list for user with no published albums (no auth)."""
    # Use a user_id with no data so result is always empty regardless of test order
    no_data_user_id = "00000000-0000-0000-0000-000000000001"
    response = await client.get(
        "/image/public",
        params={"user_id": no_data_user_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_public_images(client, published_album_with_image):
    """Test listing public images returns only images from published albums (no auth)."""
    response = await client.get(
        "/image/public",
        params={"user_id": str(TEST_USER_ID)},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    img = data[0]
    assert "id" in img
    assert "slug" in img
    assert "image_url" in img
    assert "width" in img
    assert "height" in img


@pytest.mark.asyncio
async def test_get_public_image_by_slug(client, published_album_with_image):
    """Test getting a single public image by slug (no auth)."""
    slug = published_album_with_image["image"]["slug"]
    response = await client.get(
        f"/image/public/{slug}",
        params={"user_id": str(TEST_USER_ID)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == slug
    assert data["image_url"] == "https://test.example.com/storage/images/fake.png"
    assert data["width"] == 1
    assert data["height"] == 1


@pytest.mark.asyncio
async def test_get_public_image_by_slug_not_found(client):
    """Test getting a non-existent public image by slug returns 404 (no auth)."""
    response = await client.get(
        "/image/public/nonexistent-slug",
        params={"user_id": str(TEST_USER_ID)},
    )
    assert response.status_code == 404


# === Auth-required / upload tests ===


@pytest.fixture
def tiny_png():
    """Minimal valid 1x1 PNG bytes."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

@pytest.fixture
def mock_storage():
    """Mock Supabase storage so tests don't hit real Supabase (avoids 409 Duplicate, no credentials)."""
    with patch("app.features.gallery.service.SupabaseStorageClient") as MockStorage:
        mock_instance = MagicMock()
        mock_instance.upload_image = AsyncMock(
            return_value="https://test.example.com/storage/images/fake.png"
        )
        mock_instance.delete_image = AsyncMock(return_value=True)
        MockStorage.return_value = mock_instance
        yield MockStorage


@pytest.fixture
async def created_images(client, mock_user_token, tiny_png, mock_storage):
    """Create an album and upload one image for tests that need an existing image."""
    album_response = await client.post(
        "/album/",
        json={"title": "Test Album", "is_published": False},
    )
    assert album_response.status_code == 201
    album = album_response.json()
    upload_response = await client.post(
        f"/image/{album['id']}",
        files=[("files", ("test.png", tiny_png, "image/png"))],
    )
    assert upload_response.status_code == 201
    images = upload_response.json()
    return images[0]

@pytest.mark.asyncio
async def test_upload_image(client, tiny_png, mock_user_token, mock_storage):
    """Test uploading an image to an album works (storage mocked to avoid hitting Supabase)."""
    # Create an album first
    album_response = await client.post(
        "/album/",
        json={"title": "Youth Camp", "is_published": False},
    )
    assert album_response.status_code == 201
    album = album_response.json()
    album_id = album["id"]

    response = await client.post(
        f"/image/{album_id}",
        files=[("files", ("test.png", tiny_png, "image/png"))],
    )
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["slug"]
    assert data[0]["image_url"] == "https://test.example.com/storage/images/fake.png"
    assert data[0]["width"] == 1
    assert data[0]["height"] == 1


@pytest.mark.asyncio
async def test_delete_image(client, mock_user_token, created_images, mock_storage):
    """Test deleting an image returns 204 (auth required, storage mocked)."""
    image_id = created_images["id"]
    response = await client.delete(f"/image/{image_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_image_not_found(client, mock_user_token):
    """Test deleting a non-existent image returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/image/{fake_id}")
    assert response.status_code == 404


# === Album tests (auth required) ===


@pytest.fixture
async def created_album(client, mock_user_token):
    """Create an album for tests that need an existing album."""
    response = await client.post(
        "/album/",
        json={"title": "My Album", "is_published": False},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_album(client, mock_user_token):
    """Test creating an album works."""
    response = await client.post(
        "/album/",
        json={"title": "New Gallery", "is_published": True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Gallery"
    assert data["is_published"] is True
    assert "id" in data
    assert "slug" in data


@pytest.mark.asyncio
async def test_list_albums(client, mock_user_token, created_album):
    """Test listing all albums for the user."""
    response = await client.get("/album/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Find our album (order may vary due to other tests / shared DB)
    album = next((a for a in data if a["id"] == created_album["id"]), None)
    assert album is not None
    assert album["title"] == "My Album"
    assert "slug" in album
    assert "images" in album


@pytest.mark.asyncio
async def test_get_album(client, mock_user_token, created_album):
    """Test getting a single album by ID."""
    album_id = created_album["id"]
    response = await client.get(f"/album/{album_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == album_id
    assert data["title"] == "My Album"
    assert data["is_published"] is False
    assert "images" in data


@pytest.mark.asyncio
async def test_get_album_not_found(client, mock_user_token):
    """Test getting a non-existent album returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/album/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_album(client, mock_user_token, created_album):
    """Test updating an album (PATCH)."""
    album_id = created_album["id"]
    response = await client.patch(
        f"/album/{album_id}",
        json={"title": "Updated Title", "is_published": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["is_published"] is True


@pytest.mark.asyncio
async def test_delete_album(client, mock_user_token, created_album):
    """Test deleting an album returns 204."""
    album_id = created_album["id"]
    response = await client.delete(f"/album/{album_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_album_not_found(client, mock_user_token):
    """Test deleting a non-existent album returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/album/{fake_id}")
    assert response.status_code == 404

