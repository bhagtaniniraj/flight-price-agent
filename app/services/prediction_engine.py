import random
from datetime import date, timedelta
from app.schemas import PredictionResponse, PricePoint


def generate_prediction(
    origin: str,
    destination: str,
    travel_date: str,
    avg_price: float,
) -> PredictionResponse:
    """Algorithmic price prediction based on route, date, and advance purchase."""
    today = date.today()
    try:
        dep = date.fromisoformat(travel_date)
    except ValueError:
        dep = today + timedelta(days=30)

    days_out = (dep - today).days

    if days_out <= 7:
        trend = "rising"
        recommendation = "buy_now"
        confidence = 0.90
        predicted_change = 1.15
    elif days_out <= 14:
        trend = "rising"
        recommendation = "buy_now"
        confidence = 0.80
        predicted_change = 1.08
    elif days_out <= 30:
        trend = "stable"
        recommendation = "buy_now"
        confidence = 0.65
        predicted_change = 1.02
    elif days_out <= 60:
        trend = "falling"
        recommendation = "wait"
        confidence = 0.60
        predicted_change = 0.95
    else:
        trend = "stable"
        recommendation = "wait"
        confidence = 0.55
        predicted_change = 0.98

    month = dep.month
    if month in (6, 7, 8, 12):
        if trend != "rising":
            trend = "rising"
        recommendation = "buy_now"
        confidence = min(confidence + 0.10, 0.95)
        predicted_change *= 1.05

    predicted_price = round(avg_price * predicted_change, 2)

    rng = random.Random(f"{origin}{destination}{travel_date}")
    history = []
    price = avg_price * 0.95
    for i in range(14, 0, -1):
        d = today - timedelta(days=i)
        price = price * (1 + rng.uniform(-0.03, 0.04))
        history.append(PricePoint(date=d.isoformat(), price=round(price, 2)))

    return PredictionResponse(
        origin=origin,
        destination=destination,
        travel_date=travel_date,
        current_avg_price=round(avg_price, 2),
        predicted_price=predicted_price,
        trend=trend,
        recommendation=recommendation,
        confidence=round(confidence, 2),
        price_history=history,
    )
