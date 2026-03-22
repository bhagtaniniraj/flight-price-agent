#!/usr/bin/env python3
"""Test Amadeus flight price API.

Usage:
    python scripts/test_amadeus_prices.py --origin JFK --destination LAX --date 2025-08-15
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
from app.schemas.flight import FlightSearchRequest
from app.services.amadeus_service import AmadeusService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Amadeus flight search API")
    parser.add_argument("--origin", default="JFK", help="Origin IATA code (default: JFK)")
    parser.add_argument("--destination", default="LAX", help="Destination IATA code (default: LAX)")
    parser.add_argument("--date", default="2025-08-15", help="Departure date YYYY-MM-DD (default: 2025-08-15)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adults (default: 1)")
    parser.add_argument("--currency", default="USD", help="Currency (default: USD)")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()

    if not settings.amadeus_api_key:
        print("ERROR: AMADEUS_API_KEY is not set. Please add it to your .env file.")
        sys.exit(1)

    service = AmadeusService(settings)
    request = FlightSearchRequest(
        origin=args.origin,
        destination=args.destination,
        departure_date=args.date,
        adults=args.adults,
        currency=args.currency,
        max_results=10,
    )

    print(f"\nSearching Amadeus: {args.origin} → {args.destination} on {args.date}\n")
    try:
        offers = await service.search_flights(request)
    finally:
        await service.close()

    if not offers:
        print("No offers returned.")
        return

    # Print table header
    print(f"{'#':<4} {'Airlines':<20} {'Price':>10} {'Duration':<14} {'Segments':<8} {'Deal':<6}")
    print("-" * 70)
    for i, offer in enumerate(offers, 1):
        airlines = ", ".join(offer.airline_codes)
        deal = "✓ DEAL" if offer.is_deal else ""
        print(f"{i:<4} {airlines:<20} {offer.currency} {offer.price:>8.2f} {offer.total_duration:<14} {len(offer.segments):<8} {deal}")

    print(f"\nTotal: {len(offers)} offers | Cheapest: {offers[0].currency} {offers[0].price:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
