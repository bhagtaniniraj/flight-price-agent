#!/usr/bin/env python3
"""Train the flight price prediction model from historical data.

Usage:
    python scripts/train_model.py --data data/historical_prices.csv
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from app.ml.price_predictor import MODEL_DIR, PricePredictor

FEATURE_COLS = [
    "days_until_departure",
    "price",          # current price (used as feature for future prediction)
    "departure_dow",
    "departure_month",
    "adults",
    "is_weekend",
    "is_busy_month",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the price prediction model")
    parser.add_argument(
        "--data",
        default="data/historical_prices.csv",
        help="Path to historical prices CSV (default: data/historical_prices.csv)",
    )
    parser.add_argument(
        "--output",
        default=str(MODEL_DIR / "price_predictor.pkl"),
        help="Path to save the trained model",
    )
    return parser.parse_args()


def build_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Build feature matrix and target vector from historical data."""
    # Target: what will the price be at departure (approximate with price itself shifted)
    # For training: use current price features to predict a future price
    # We simulate "future price" as current_price * some multiplier for demonstration
    df = df.copy()
    df["log_price"] = np.log1p(df["price"])
    df["sqrt_days"] = np.sqrt(df["days_until_departure"].clip(lower=0))

    feature_cols = [
        "days_until_departure",
        "price",
        "departure_dow",
        "departure_month",
        "adults",
        "is_weekend",
        "is_busy_month",
        "log_price",
        "sqrt_days",
    ]
    # Pad to 11 features to match FeatureEngineer output (add 2 dummy cols)
    df["is_popular_route"] = 0.0
    df["departure_day"] = 15.0
    all_cols = feature_cols + ["is_popular_route", "departure_day"]

    X = df[all_cols].values.astype(np.float64)
    # Target: next-day price (simulated as price + small variation)
    rng = np.random.default_rng(42)
    noise = rng.normal(0, df["price"].values * 0.05)
    y = (df["price"].values + noise).clip(min=50.0)
    return X, y


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        print("Run: python scripts/seed_historical_data.py first.")
        sys.exit(1)

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  Rows: {len(df)}")

    X, y = build_features(df)
    print(f"  Features shape: {X.shape}")

    predictor = PricePredictor()
    print("\nTraining GradientBoostingRegressor...")
    metrics = predictor.train(X, y)
    print(f"  MAE:  {metrics['mae']:.2f}")
    print(f"  R²:   {metrics['r2']:.4f}")

    output_path = args.output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    predictor.save_model(output_path)
    print(f"\nModel saved to {output_path}")


if __name__ == "__main__":
    main()
