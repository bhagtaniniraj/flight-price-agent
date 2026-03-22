import pytest


@pytest.mark.asyncio
async def test_search_airports_by_city(client):
    response = await client.get("/api/airports?q=new")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_airport_by_code(client):
    response = await client.get("/api/airports/JFK")
    assert response.status_code == 200
    data = response.json()
    assert data["iata_code"] == "JFK"
    assert data["city"] == "New York"


@pytest.mark.asyncio
async def test_get_airport_not_found(client):
    response = await client.get("/api/airports/XXX")
    assert response.status_code == 404
