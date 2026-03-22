#!/usr/bin/env python3
"""Compare flight prices across all configured providers.

Usage:
    python scripts/compare_prices.py --origin JFK --destination LAX --date 2025-08-15
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
from app.schemas.flight import FlightSearchRequest
from app.services.aggregator import FlightAggregator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare flight prices across all providers")
    parser.add_argument("--origin", default="JFK")
    parser.add_argument("--destination", default="LAX")
    parser.add_argument("--date", default="2025-08-15")
    parser.add_argument("--adults", type=int, default=1)
    parser.add_argument("--currency", default="USD")
    return parser.parse_args()


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

    print(f"\n{'='*70}")
    print(f"  Flight Price Comparison: {args.origin} → {args.destination} on {args.date}")
    print(f"{'='*70}\n")

    try:
        response = await aggregator.search(request)
    finally:
        await aggregator.close()

    if not response.offers:
        print("No offers found from any provider.")
        return

    print(f"Providers queried: {', '.join(response.providers_queried)}")
    print(f"Total offers found: {response.total_results}")
    print(f"Search ID: {response.search_id}\n")

    print(f"{'#':<4} {'Source':<10} {'Airlines':<18} {'Price':>10} {'Duration':<14} {'Deal'}")
    print("-" * 70)
    for i, offer in enumerate(response.offers[:20], 1):
        airlines = ", ".join(offer.airline_codes)[:16]
        deal = "⭐ DEAL" if offer.is_deal else ""
        print(f"{i:<4} {offer.source:<10} {airlines:<18} {offer.currency} {offer.price:>8.2f} {offer.total_duration:<14} {deal}")

    if response.cheapest_price is not None:
        print(f"\n🏆 Cheapest price: {args.currency} {response.cheapest_price:.2f} from {response.offers[0].source}")


if __name__ == "__main__":
    asyncio.run(main())
