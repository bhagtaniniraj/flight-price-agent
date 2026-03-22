#!/usr/bin/env python3
"""Generate sample historical flight price data for ML training.

Creates data/historical_prices.csv with realistic price patterns.

Usage:
    python scripts/seed_historical_data.py --rows 2000
"""
import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "historical_prices.csv"

ROUTES = [
    ("JFK", "LAX", 280), ("LAX", "JFK", 290), ("ORD", "ATL", 160),
    ("ATL", "ORD", 155), ("DFW", "DEN", 180), ("SFO", "SEA", 140),
    ("LHR", "CDG", 120), ("CDG", "LHR", 115), ("BOS", "MIA", 200),
    ("LAX", "ORD", 220),
]


def generate_price(base_price: float, days_until_dep: int, month: int) -> float:
    """Generate a realistic price with temporal and seasonal effects."""
    # Prices tend to rise as departure approaches within 14 days
    proximity_factor = 1.0 + max(0, (14 - days_until_dep) / 14) * 0.4
    # Summer and December are more expensive
    seasonal_factor = 1.25 if month in (6, 7, 8, 12) else 1.0
    # Add random noise
    noise = np.random.normal(0, base_price * 0.08)
    return max(50.0, base_price * proximity_factor * seasonal_factor + noise)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed historical flight price data")
    parser.add_argument("--rows", type=int, default=2000, help="Number of rows to generate")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(42)
    np.random.seed(42)

    records = []
    base_date = datetime(2024, 1, 1)

    for _ in range(args.rows):
        origin, destination, base_price = random.choice(ROUTES)
        days_until_dep = random.randint(1, 180)
        departure_dt = base_date + timedelta(days=random.randint(0, 365))
        search_dt = departure_dt - timedelta(days=days_until_dep)
        price = generate_price(base_price, days_until_dep, departure_dt.month)

        records.append({
            "origin": origin,
            "destination": destination,
            "departure_date": departure_dt.strftime("%Y-%m-%d"),
            "search_date": search_dt.strftime("%Y-%m-%d"),
            "days_until_departure": days_until_dep,
            "price": round(price, 2),
            "currency": "USD",
            "adults": random.choice([1, 1, 1, 2]),
            "departure_month": departure_dt.month,
            "departure_dow": departure_dt.weekday(),
            "is_weekend": int(departure_dt.weekday() >= 5),
            "is_busy_month": int(departure_dt.month in (6, 7, 8, 12)),
        })

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Generated {len(df)} rows → {OUTPUT_FILE}")
    print(df.describe())


if __name__ == "__main__":
    main()
