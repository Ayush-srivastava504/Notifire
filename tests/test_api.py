import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_send_notification():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/notify",
            json={
                "type": "email",
                "recipient": "test@example.com",
                "payload": {"subject": "Test", "body": "Hello"},
                "max_retries": 3
            },
            headers={"X-API-Key": "test-key-123"}
        )
        assert response.status_code == 200
        assert "message_id" in response.json()

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"