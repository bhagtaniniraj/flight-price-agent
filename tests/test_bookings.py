import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_create_and_get_booking(client):
    dep = (date.today() + timedelta(days=7)).isoformat()
    flights = await client.get(f"/api/flights/search?origin=JFK&destination=LAX&departure_date={dep}")
    assert flights.status_code == 200
    flight_list = flights.json()
    assert len(flight_list) > 0
    flight_id = flight_list[0]["id"]

    booking_data = {
        "flight_id": flight_id,
        "passenger_name": "John Doe",
        "passenger_email": "john@example.com",
        "passenger_count": 1,
        "seat_class": "economy",
    }
    resp = await client.post("/api/bookings", json=booking_data)
    assert resp.status_code == 201
    b = resp.json()
    assert b["booking_reference"]
    assert len(b["booking_reference"]) == 6
    assert b["status"] == "confirmed"

    get_resp = await client.get(f"/api/bookings/{b['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["booking_reference"] == b["booking_reference"]


@pytest.mark.asyncio
async def test_list_bookings_by_email(client):
    dep = (date.today() + timedelta(days=5)).isoformat()
    flights = await client.get(f"/api/flights/search?origin=LHR&destination=CDG&departure_date={dep}")
    if flights.status_code == 200 and flights.json():
        flight_id = flights.json()[0]["id"]
        await client.post("/api/bookings", json={
            "flight_id": flight_id,
            "passenger_name": "Jane Smith",
            "passenger_email": "jane@test.com",
            "passenger_count": 1,
            "seat_class": "economy",
        })
    resp = await client.get("/api/bookings?email=jane@test.com")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_cancel_booking(client):
    dep = (date.today() + timedelta(days=10)).isoformat()
    flights = await client.get(f"/api/flights/search?origin=JFK&destination=LAX&departure_date={dep}")
    assert flights.status_code == 200
    flight_list = flights.json()
    assert len(flight_list) > 0
    flight_id = flight_list[0]["id"]

    resp = await client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Cancel Me",
        "passenger_email": "cancel@test.com",
        "passenger_count": 1,
        "seat_class": "economy",
    })
    assert resp.status_code == 201
    bid = resp.json()["id"]

    cancel_resp = await client.delete(f"/api/bookings/{bid}")
    assert cancel_resp.status_code == 204

    get_resp = await client.get(f"/api/bookings/{bid}")
    assert get_resp.json()["status"] == "cancelled"
