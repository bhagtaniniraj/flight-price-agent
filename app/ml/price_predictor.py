"""Flight price prediction using gradient boosting."""
import logging
import os
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "models"


class PricePredictor:
    """Predicts flight prices using a GradientBoostingRegressor."""

    def __init__(self) -> None:
        self._model: GradientBoostingRegressor | None = None
        self._scaler: StandardScaler | None = None
        self._is_trained = False
        self._try_load_model()

    def _try_load_model(self) -> None:
        """Load persisted model if available."""
        model_path = MODEL_DIR / "price_predictor.pkl"
        if model_path.exists():
            try:
                self.load_model(str(model_path))
            except Exception as exc:
                logger.warning("Could not load saved model: %s", exc)

    def train(self, X: np.ndarray, y: np.ndarray) -> dict[str, float]:
        """Train the price prediction model and return training metrics."""
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, r2_score

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

        self._scaler = StandardScaler()
        X_train_scaled = self._scaler.fit_transform(X_train)
        X_val_scaled = self._scaler.transform(X_val)

        self._model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )
        self._model.fit(X_train_scaled, y_train)
        self._is_trained = True

        y_pred = self._model.predict(X_val_scaled)
        mae = float(mean_absolute_error(y_val, y_pred))
        r2 = float(r2_score(y_val, y_pred))
        logger.info("Model trained: MAE=%.2f, R2=%.4f", mae, r2)
        return {"mae": mae, "r2": r2}

    def predict(self, features: np.ndarray) -> tuple[float, float]:
        """Return (predicted_price, confidence) for a single feature vector."""
        if not self._is_trained or self._model is None or self._scaler is None:
            # Fallback heuristic when model is not yet trained
            base = float(features.flatten()[0]) if features.size > 0 else 300.0
            return base * 1.02, 0.5

        x = features.reshape(1, -1)
        x_scaled = self._scaler.transform(x)
        prediction = float(self._model.predict(x_scaled)[0])

        # Estimate confidence from tree variance
        individual_preds = np.array([
            est.predict(x_scaled)[0] for est in self._model.estimators_[:, 0]
        ])
        std = float(np.std(individual_preds))
        confidence = max(0.0, min(1.0, 1.0 - std / (abs(prediction) + 1e-6)))
        return prediction, confidence

    def save_model(self, path: str) -> None:
        """Persist the trained model and scaler to disk."""
        if not self._is_trained:
            raise ValueError("Model has not been trained yet.")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"model": self._model, "scaler": self._scaler}, f)
        logger.info("Model saved to %s", path)

    def load_model(self, path: str) -> None:
        """Load a previously saved model and scaler from disk."""
        with open(path, "rb") as f:
            payload = pickle.load(f)  # noqa: S301
        self._model = payload["model"]
        self._scaler = payload["scaler"]
        self._is_trained = True
        logger.info("Model loaded from %s", path)
