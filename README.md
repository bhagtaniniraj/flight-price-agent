# ✈️ Flight Price Agent

[![CI](https://github.com/your-org/flight-price-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/flight-price-agent/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered flight price agent that searches **Amadeus**, **Kiwi/Tequila**, and **Duffel** simultaneously, deduplicates results, marks deals, and predicts whether prices will rise or fall — all in a single API call.

---

## ✨ Features

- 🔍 **Multi-provider search** — queries Amadeus, Kiwi/Tequila, and Duffel in parallel
- 🧹 **Deduplication** — removes duplicate itineraries across providers
- ⭐ **Deal detection** — flags offers priced >20% below median as deals
- 🤖 **Price prediction** — ML-based buy/wait recommendation with confidence score
- 🔔 **Price alerts** — create alerts and get notified when target price is hit
- 📊 **Skyscanner comparison** — compare your best price against Skyscanner
- 🐳 **Docker ready** — full docker-compose stack with PostgreSQL and Redis

---

## 🏗️ Architecture

```
flight-price-agent/
├── app/
│   ├── api/
│   │   ├── dependencies.py       # FastAPI DI factories
│   │   └── routes/
│   │       ├── search.py         # POST /api/v1/search/
│   │       ├── alerts.py         # CRUD /api/v1/alerts/
│   │       └── predictions.py    # POST /api/v1/predict/
│   ├── services/
│   │   ├── amadeus_service.py    # Amadeus API client
│   │   ├── kiwi_service.py       # Kiwi/Tequila API client
│   │   ├── duffel_service.py     # Duffel API client
│   │   ├── aggregator.py         # Parallel search + dedup
│   │   └── alert_service.py      # In-memory alert store
│   ├── ml/
│   │   ├── price_predictor.py    # GradientBoosting model
│   │   ├── feature_engineering.py
│   │   └── anomaly_detector.py
│   ├── db/
│   │   ├── database.py           # SQLAlchemy async engine
│   │   └── models.py             # ORM models
│   ├── cache/
│   │   └── redis_client.py       # Async Redis cache
│   ├── schemas/                  # Pydantic v2 models
│   ├── config.py                 # Pydantic Settings
│   └── main.py                   # FastAPI app
├── scripts/
│   ├── test_amadeus_prices.py
│   ├── test_kiwi_prices.py
│   ├── compare_prices.py
│   ├── compare_with_skyscanner.py
│   ├── seed_historical_data.py
│   └── train_model.py
└── tests/
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

```bash
# 1. Clone and configure
git clone https://github.com/your-org/flight-price-agent.git
cd flight-price-agent
cp .env.example .env
# Edit .env with your API keys

# 2. Start everything
docker compose up --build

# 3. Open docs
open http://localhost:8000/docs
```

### Option B — Local development

```bash
# Prerequisites: Python 3.11+, PostgreSQL, Redis

python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
# Edit .env with your API keys and local DB/Redis URLs

uvicorn app.main:app --reload
```

---

## 🔑 Getting API Keys

| Provider | URL | Cost |
|----------|-----|------|
| Amadeus | https://developers.amadeus.com | Free (test) |
| Kiwi/Tequila | https://tequila.kiwi.com | Free |
| Duffel | https://duffel.com | Free (test) |
| Skyscanner | https://partners.skyscanner.net | Apply |

Add keys to your `.env` file:

```env
AMADEUS_API_KEY=your_key
AMADEUS_API_SECRET=your_secret
KIWI_API_KEY=your_key
DUFFEL_API_TOKEN=your_token
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/search/` | Search flights across all providers |
| `GET` | `/api/v1/search/compare` | Compare prices via query params |
| `POST` | `/api/v1/alerts/` | Create a price alert |
| `GET` | `/api/v1/alerts/` | List all alerts |
| `GET` | `/api/v1/alerts/{id}` | Get alert by ID |
| `PATCH` | `/api/v1/alerts/{id}` | Update alert |
| `DELETE` | `/api/v1/alerts/{id}` | Delete alert |
| `POST` | `/api/v1/predict/` | Predict future price & get recommendation |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

---

## 🌍 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AMADEUS_API_KEY` | Amadeus client ID | — |
| `AMADEUS_API_SECRET` | Amadeus client secret | — |
| `AMADEUS_BASE_URL` | Amadeus base URL | `https://test.api.amadeus.com` |
| `KIWI_API_KEY` | Kiwi/Tequila API key | — |
| `KIWI_BASE_URL` | Kiwi base URL | `https://api.tequila.kiwi.com` |
| `DUFFEL_API_TOKEN` | Duffel bearer token | — |
| `DUFFEL_BASE_URL` | Duffel base URL | `https://api.duffel.com` |
| `DATABASE_URL` | Async PostgreSQL URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `ENVIRONMENT` | `development` / `production` | `development` |
| `DEBUG` | Enable SQLAlchemy echo | `true` |

---

## 🔧 Usage Examples

### Search flights

```bash
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2025-08-15",
    "adults": 1,
    "currency": "USD"
  }'
```

### Compare prices (GET)

```bash
curl "http://localhost:8000/api/v1/search/compare?origin=JFK&destination=LAX&departure_date=2025-08-15"
```

### Predict price trend

```bash
curl -X POST http://localhost:8000/api/v1/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2025-08-15",
    "days_until_departure": 30,
    "current_price": 350.00,
    "adults": 1
  }'
```

### Create a price alert

```bash
curl -X POST http://localhost:8000/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2025-08-15",
    "target_price": 250.00,
    "currency": "USD",
    "email": "you@example.com"
  }'
```

---

## 🏃 Running Price Comparisons

```bash
# Compare all providers for a route
python scripts/compare_prices.py --origin JFK --destination LAX --date 2025-08-15

# Compare against Skyscanner and log results
python scripts/compare_with_skyscanner.py --origin JFK --destination LAX --date 2025-08-15 --skyscanner-price 399.00

# Generate historical data and train ML model
python scripts/seed_historical_data.py --rows 5000
python scripts/train_model.py
```

---

## 🧪 Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing tests/

# Single test file
pytest tests/test_aggregator.py -v
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run linting: `ruff check . && mypy app/`
5. Run tests: `pytest`
6. Submit a pull request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
