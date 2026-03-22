from datetime import date, datetime


def compute_price(base_price: float, seat_class: str, departure_dt: datetime) -> float:
    """Apply dynamic pricing modifiers."""
    dep_date = departure_dt.date() if isinstance(departure_dt, datetime) else departure_dt
    today = date.today()
    days_until = (dep_date - today).days

    if days_until <= 3:
        urgency = 1.35
    elif days_until <= 7:
        urgency = 1.20
    elif days_until <= 14:
        urgency = 1.10
    elif days_until <= 30:
        urgency = 1.05
    else:
        urgency = 1.0

    dow = dep_date.weekday()
    weekend = 1.08 if dow in (4, 5, 6) else 1.0

    month = dep_date.month
    peak = 1.12 if month in (6, 7, 8, 12) else 1.0

    price = base_price * urgency * weekend * peak

    if seat_class == "premium_economy":
        price *= 1.5
    elif seat_class == "business":
        price = base_price * 3.0 * urgency * weekend * peak
    elif seat_class == "first":
        price = base_price * 6.0 * urgency * weekend * peak

    return round(price, 2)
