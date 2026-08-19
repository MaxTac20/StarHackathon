from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_api_route_is_json_404(client: AsyncClient) -> None:
    response = await client.get("/api/not-a-route")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "API endpoint not found"
