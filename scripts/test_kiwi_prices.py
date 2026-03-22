#!/usr/bin/env python3
"""Test Kiwi/Tequila flight price API.

Usage:
    python scripts/test_kiwi_prices.py --origin JFK --destination LAX --date 2025-08-15
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
from app.services.kiwi_service import KiwiService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Kiwi/Tequila flight search API")
    parser.add_argument("--origin", default="JFK", help="Origin IATA code (default: JFK)")
    parser.add_argument("--destination", default="LAX", help="Destination IATA code (default: LAX)")
    parser.add_argument("--date", default="2025-08-15", help="Departure date YYYY-MM-DD (default: 2025-08-15)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adults (default: 1)")
    parser.add_argument("--currency", default="USD", help="Currency (default: USD)")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()

    if not settings.kiwi_api_key:
        print("ERROR: KIWI_API_KEY is not set. Please add it to your .env file.")
        sys.exit(1)

    service = KiwiService(settings)
    request = FlightSearchRequest(
        origin=args.origin,
        destination=args.destination,
        departure_date=args.date,
        adults=args.adults,
        currency=args.currency,
        max_results=10,
    )

    print(f"\nSearching Kiwi/Tequila: {args.origin} → {args.destination} on {args.date}\n")
    try:
        offers = await service.search_flights(request)
    finally:
        await service.close()

    if not offers:
        print("No offers returned.")
        return

    print(f"{'#':<4} {'Airlines':<20} {'Price':>10} {'Duration':<14} {'Deep Link'}")
    print("-" * 80)
    for i, offer in enumerate(offers, 1):
        airlines = ", ".join(offer.airline_codes)
        link = (offer.deep_link or "")[:40]
        print(f"{i:<4} {airlines:<20} {offer.currency} {offer.price:>8.2f} {offer.total_duration:<14} {link}")

    print(f"\nTotal: {len(offers)} offers | Cheapest: {offers[0].currency} {offers[0].price:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
