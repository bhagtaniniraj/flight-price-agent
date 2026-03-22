import pytest


@pytest.mark.asyncio
async def test_create_and_list_alert(client):
    resp = await client.post("/api/alerts", json={
        "origin_iata": "JFK",
        "destination_iata": "LAX",
        "target_price": 300.0,
        "user_email": "alert@test.com",
    })
    assert resp.status_code == 201
    a = resp.json()
    assert a["origin_iata"] == "JFK"

    list_resp = await client.get("/api/alerts?email=alert@test.com")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_delete_alert(client):
    resp = await client.post("/api/alerts", json={
        "origin_iata": "LHR",
        "destination_iata": "FRA",
        "target_price": 150.0,
        "user_email": "del@test.com",
    })
    assert resp.status_code == 201
    aid = resp.json()["id"]

    del_resp = await client.delete(f"/api/alerts/{aid}")
    assert del_resp.status_code == 204
