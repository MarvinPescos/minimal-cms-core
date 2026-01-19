import pytest
from httpx import AsyncClient

# Test for endpoint logic

# @pytest.mark.asyncio
# async def test_health_check(client: AsyncClient):
#     response = await client.get("/doc")
#     assert response.status_code == 200

# @pytest.mark.asyncio
# async def test_get_profile_unauthorized(client: AsyncClient):
#     """Fail if no token provided"""
#     response = await client.get("/auth/me")
#     assert response.status_code == 401

# @pytest.mark.asyncio
# async def test_get_profile_success(client: AsyncClient, mock_user_token):
#     """Success if mocked token provided"""
#     response = await client.get("/auth/me")
#     assert response.status_code == 200
#     assert response.json()["email"] == "test@example.com"
