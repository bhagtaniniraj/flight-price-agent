"""Anomaly detection for flight prices using z-score method."""
import logging
import statistics
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result of anomaly detection on a price."""

    price: float
    z_score: float
    is_anomaly: bool
    direction: str  # "low", "high", or "normal"
    deviation_pct: float


class AnomalyDetector:
    """Detects price anomalies (unusually cheap or expensive fares) using z-scores."""

    def __init__(self, threshold: float = 2.0) -> None:
        self.threshold = threshold

    def detect(self, prices: list[float]) -> list[AnomalyResult]:
        """Detect anomalies in a list of prices.

        Args:
            prices: List of prices to analyse.

        Returns:
            List of AnomalyResult objects, one per input price.
        """
        if len(prices) < 2:
            return [
                AnomalyResult(price=p, z_score=0.0, is_anomaly=False, direction="normal", deviation_pct=0.0)
                for p in prices
            ]

        mean = statistics.mean(prices)
        std = statistics.stdev(prices)

        results: list[AnomalyResult] = []
        for price in prices:
            if std == 0:
                z = 0.0
            else:
                z = (price - mean) / std

            is_anomaly = abs(z) > self.threshold
            if z < -self.threshold:
                direction = "low"
            elif z > self.threshold:
                direction = "high"
            else:
                direction = "normal"

            deviation_pct = ((price - mean) / mean * 100) if mean != 0 else 0.0

            results.append(
                AnomalyResult(
                    price=price,
                    z_score=round(z, 4),
                    is_anomaly=is_anomaly,
                    direction=direction,
                    deviation_pct=round(deviation_pct, 2),
                )
            )
        return results

    def get_deals(self, prices: list[float]) -> list[int]:
        """Return indices of prices that are anomalously cheap."""
        results = self.detect(prices)
        return [i for i, r in enumerate(results) if r.direction == "low"]
