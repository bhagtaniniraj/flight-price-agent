import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_prediction_jfk_lax(client):
    travel = (date.today() + timedelta(days=30)).isoformat()
    resp = await client.get(f"/api/predictions?origin=JFK&destination=LAX&travel_date={travel}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["origin"] == "JFK"
    assert data["destination"] == "LAX"
    assert data["trend"] in ("rising", "falling", "stable")
    assert data["recommendation"] in ("buy_now", "wait")
    assert 0.0 <= data["confidence"] <= 1.0
    assert len(data["price_history"]) == 14


@pytest.mark.asyncio
async def test_prediction_not_found(client):
    resp = await client.get("/api/predictions?origin=XXX&destination=YYY&travel_date=2025-12-01")
    assert resp.status_code == 404
