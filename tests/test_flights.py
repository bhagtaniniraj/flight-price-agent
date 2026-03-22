import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_search_flights_returns_results(client):
    dep = (date.today() + timedelta(days=7)).isoformat()
    response = await client.get(f"/api/flights/search?origin=JFK&destination=LAX&departure_date={dep}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_search_flights_sorted_by_price(client):
    dep = (date.today() + timedelta(days=7)).isoformat()
    response = await client.get(f"/api/flights/search?origin=JFK&destination=LAX&departure_date={dep}&sort_by=price")
    assert response.status_code == 200
    prices = [f["price"] for f in response.json()]
    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_search_flights_max_stops_filter(client):
    dep = (date.today() + timedelta(days=7)).isoformat()
    response = await client.get(f"/api/flights/search?origin=JFK&destination=LAX&departure_date={dep}&max_stops=0")
    assert response.status_code == 200
    for f in response.json():
        assert f["stops"] == 0


@pytest.mark.asyncio
async def test_search_invalid_date(client):
    response = await client.get("/api/flights/search?origin=JFK&destination=LAX&departure_date=invalid")
    assert response.status_code == 400
