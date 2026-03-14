"""
backend/ml/prediction_model.py
XGBoost-based binary classifier (UP / DOWN) with scikit-learn wrapper.
Trained on technical features + LLM sentiment scores.
"""
from __future__ import annotations

import pickle

import numpy as np
from loguru import logger

from backend.core.config import settings

FEATURE_COLS = [
    "change_1d_pct", "change_5d_pct",
    "sma_crossover", "macd", "macd_hist",
    "rsi", "bb_pct", "vol_ratio",
    "sentiment_score", "confidence",
    "impact_avg",
]


class StockPredictor:
    """
    XGBoost binary classifier: 1 = UP, 0 = DOWN over 2-3 days.
    Falls back to a heuristic model when insufficient training data.
    """

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.model_path = settings.ml_model_dir / f"{self.ticker}_xgb.pkl"
        self.model = self._load_or_init()

    # ─── init ──────────────────────────────────────────────────────────────────

    def _load_or_init(self):
        if self.model_path.exists():
            with open(self.model_path, "rb") as f:
                logger.info(f"Loaded existing model for {self.ticker}")
                return pickle.load(f)
        return self._build_default_model()

    def _build_default_model(self):
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=42,
            )
        except ImportError:
            from sklearn.ensemble import GradientBoostingClassifier
            return GradientBoostingClassifier(n_estimators=100, random_state=42)

    # ─── feature vector ────────────────────────────────────────────────────────

    @staticmethod
    def build_feature_vector(
        tech_features: dict,
        sentiment_data: dict,
        article_sentiments: list[dict],
    ) -> np.ndarray:
        impact_scores = [
            a.get("impact_score", 0.0) for a in article_sentiments
            if isinstance(a.get("impact_score"), (int, float))
        ]
        impact_avg = float(np.mean(impact_scores)) if impact_scores else 0.0

        vec = [
            tech_features.get("change_1d_pct", 0.0),
            tech_features.get("change_5d_pct", 0.0),
            tech_features.get("sma_crossover", 0),
            tech_features.get("macd", 0.0),
            tech_features.get("macd_hist", 0.0),
            tech_features.get("rsi", 50.0),
            tech_features.get("bb_pct", 0.5),
            tech_features.get("vol_ratio", 1.0),
            sentiment_data.get("sentiment_score", 0.0),
            sentiment_data.get("confidence", 0.0),
            impact_avg,
        ]
        return np.array(vec, dtype=np.float32).reshape(1, -1)

    # ─── predict ───────────────────────────────────────────────────────────────

    def predict(self, feature_vec: np.ndarray) -> dict:
        """
        Returns {direction, probability, confidence_band}.
        Falls back to heuristic if model not yet trained.
        """
        try:
            if not hasattr(self.model, "feature_importances_"):
                return self._heuristic_predict(feature_vec)
            prob = self.model.predict_proba(feature_vec)[0]
            direction = "UP" if prob[1] > 0.5 else "DOWN"
            probability = float(max(prob))
            confidence = (
                "HIGH" if probability > 0.7
                else "MEDIUM" if probability > 0.55
                else "LOW"
            )
            return {
                "direction": direction,
                "probability": round(probability, 4),
                "confidence_band": confidence,
            }
        except Exception as e:
            logger.warning(f"Prediction model error, using heuristic: {e}")
            return self._heuristic_predict(feature_vec)

    def _heuristic_predict(self, vec: np.ndarray) -> dict:
        """Rule-based fallback when model lacks training data."""
        v = vec.flatten()
        score = (
            0.3 * np.tanh(v[0] / 5)       # 1d change
            + 0.2 * np.tanh(v[1] / 10)    # 5d change
            + 0.15 * (v[7] - 1.0)          # vol ratio
            + 0.2 * v[8]                   # sentiment
            + 0.15 * v[10]                 # impact avg
        )
        prob = float(1 / (1 + np.exp(-score * 3)))  # sigmoid
        direction = "UP" if prob > 0.5 else "DOWN"
        return {
            "direction": direction,
            "probability": round(max(prob, 1 - prob), 4),
            "confidence_band": "LOW",
        }

    # ─── training ──────────────────────────────────────────────────────────────

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train/retrain the model. y: 1=UP, 0=DOWN."""
        if len(X) < 20:
            logger.warning(f"Only {len(X)} samples – skipping training.")
            return
        self.model.fit(X, y)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved for {self.ticker} ({len(X)} samples).")

    # ─── save / load state ─────────────────────────────────────────────────────

    def save(self):
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)
