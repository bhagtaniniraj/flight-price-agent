"""Feature engineering for flight price prediction."""
import logging
from datetime import datetime

import numpy as np

from app.schemas.prediction import PredictionRequest

logger = logging.getLogger(__name__)

POPULAR_ROUTES = {
    ("JFK", "LAX"), ("LAX", "JFK"), ("ORD", "ATL"), ("ATL", "ORD"),
    ("DFW", "DEN"), ("LHR", "CDG"), ("CDG", "LHR"), ("SFO", "SEA"),
}

BUSY_MONTHS = {6, 7, 8, 12}  # Summer and December


class FeatureEngineer:
    """Extracts numerical features from a PredictionRequest for ML models."""

    def extract_features(self, request: PredictionRequest) -> np.ndarray:
        """Extract feature vector from a PredictionRequest.

        Feature vector (11 dimensions):
          0: days_until_departure
          1: current_price
          2: departure_day_of_week (0=Mon … 6=Sun)
          3: departure_month (1–12)
          4: departure_day (1–31)
          5: is_weekend_departure (0/1)
          6: is_busy_month (0/1)
          7: is_popular_route (0/1)
          8: adults
          9: log(current_price)
          10: days_until_departure ** 0.5 (sqrt)

        Returns:
            A 1-D numpy array with dtype float64.
        """
        try:
            dep_date = datetime.strptime(request.departure_date, "%Y-%m-%d")
        except ValueError:
            dep_date = datetime.utcnow()

        route_pair = (request.origin.upper(), request.destination.upper())
        is_popular = 1.0 if route_pair in POPULAR_ROUTES else 0.0
        is_weekend = 1.0 if dep_date.weekday() >= 5 else 0.0
        is_busy = 1.0 if dep_date.month in BUSY_MONTHS else 0.0

        features = np.array(
            [
                float(request.days_until_departure),
                float(request.current_price),
                float(dep_date.weekday()),
                float(dep_date.month),
                float(dep_date.day),
                is_weekend,
                is_busy,
                is_popular,
                float(request.adults),
                float(np.log1p(request.current_price)),
                float(np.sqrt(max(0, request.days_until_departure))),
            ],
            dtype=np.float64,
        )
        return features
