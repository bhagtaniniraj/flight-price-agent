#!/usr/bin/env python3
"""Compare agent prices with Skyscanner prices and log results.

If SKYSCANNER_API_KEY is not set, prompts for manual entry.

Usage:
    python scripts/compare_with_skyscanner.py --origin JFK --destination LAX --date 2025-08-15
"""
import argparse
import asyncio
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
from app.schemas.flight import FlightSearchRequest
from app.services.aggregator import FlightAggregator

DATA_DIR = Path(__file__).parent.parent / "data"
COMPARISON_FILE = DATA_DIR / "comparisons.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare agent prices with Skyscanner")
    parser.add_argument("--origin", default="JFK")
    parser.add_argument("--destination", default="LAX")
    parser.add_argument("--date", default="2025-08-15")
    parser.add_argument("--adults", type=int, default=1)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--skyscanner-price", type=float, default=None,
                        help="Skyscanner price to compare against (skips manual prompt)")
    return parser.parse_args()


def get_skyscanner_price(args: argparse.Namespace) -> float:
    """Return Skyscanner price from arg or prompt user."""
    if args.skyscanner_price is not None:
        return args.skyscanner_price
    print("\nEnter the cheapest price you found on Skyscanner for this route:")
    while True:
        raw = input(f"  Skyscanner price ({args.currency}): ").strip()
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a valid number.")


def append_comparison(row: dict) -> None:
    """Append a comparison row to the CSV file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp", "origin", "destination", "date", "currency",
        "agent_price", "skyscanner_price", "savings", "savings_pct", "agent_source",
    ]
    write_header = not COMPARISON_FILE.exists()
    with open(COMPARISON_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    aggregator = FlightAggregator(settings)

    request = FlightSearchRequest(
        origin=args.origin,
        destination=args.destination,
        departure_date=args.date,
        adults=args.adults,
        currency=args.currency,
        max_results=10,
    )

    print(f"\nSearching all providers for {args.origin} → {args.destination} on {args.date}...")
    try:
        response = await aggregator.search(request)
    finally:
        await aggregator.close()

    if not response.offers:
        print("No offers found from any provider.")
        return

    agent_price = response.cheapest_price
    best_offer = response.offers[0]
    print(f"\nBest agent price: {args.currency} {agent_price:.2f} via {best_offer.source} ({', '.join(best_offer.airline_codes)})")

    sky_price = get_skyscanner_price(args)
    savings = sky_price - agent_price
    savings_pct = (savings / sky_price * 100) if sky_price > 0 else 0.0

    print(f"\n{'='*50}")
    print(f"  Agent price:      {args.currency} {agent_price:>10.2f}")
    print(f"  Skyscanner price: {args.currency} {sky_price:>10.2f}")
    print(f"  Savings:          {args.currency} {savings:>10.2f} ({savings_pct:.1f}%)")
    if savings > 0:
        print(f"  ✅ Agent beats Skyscanner by {savings_pct:.1f}%!")
    else:
        print(f"  ❌ Skyscanner is cheaper by {abs(savings):.2f}")
    print(f"{'='*50}\n")

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "origin": args.origin,
        "destination": args.destination,
        "date": args.date,
        "currency": args.currency,
        "agent_price": round(agent_price, 2),
        "skyscanner_price": round(sky_price, 2),
        "savings": round(savings, 2),
        "savings_pct": round(savings_pct, 2),
        "agent_source": best_offer.source,
    }
    append_comparison(row)
    print(f"Comparison saved to {COMPARISON_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
