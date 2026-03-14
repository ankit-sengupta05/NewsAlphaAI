"""
backend/rl/feedback_loop.py
Active Reinforcement Learning feedback loop.
Records predictions, collects actual outcomes, computes rewards,
and triggers model retraining when enough labelled samples accumulate.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import numpy as np
from loguru import logger

from backend.core.config import settings
from backend.ml.prediction_model import StockPredictor


class RLFeedbackLoop:
    """
    Implements a simple policy-gradient-inspired feedback loop:
    1. Prediction is stored with its feature vector.
    2. After N days the actual price move is checked.
    3. Reward = +1 (correct) / -1 (wrong) / 0 (unclear).
    4. Weighted samples are used to retrain the model.
    """

    def __init__(self):
        self.feedback_log = settings.rl_feedback_log
        self.feedback_log.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[dict] = self._load()

    # ─── persistence ──────────────────────────────────────────────────────────

    def _load(self) -> list[dict]:
        if not self.feedback_log.exists():
            return []
        records = []
        for line in self.feedback_log.read_text().splitlines():
            try:
                records.append(json.loads(line))
            except Exception:
                pass
        return records

    def _append(self, record: dict):
        with open(self.feedback_log, "a") as f:
            f.write(json.dumps(record) + "\n")
        self._records.append(record)

    # ─── record prediction ────────────────────────────────────────────────────

    def record_prediction(
        self,
        ticker: str,
        prediction: dict,
        feature_vec: list[float],
        price_at_prediction: float,
    ):
        record = {
            "ticker": ticker,
            "prediction": prediction,
            "feature_vec": feature_vec,
            "price_at_prediction": price_at_prediction,
            "predicted_at": datetime.utcnow().isoformat(),
            "outcome": None,
            "reward": None,
        }
        self._append(record)
        logger.info(
            f"RL: Recorded prediction for {ticker} – {prediction['direction']}"
        )

    # ─── resolve outcomes ─────────────────────────────────────────────────────

    def resolve_outcomes(self, ticker: str):
        """
        For any unresolved predictions older than 3 days, fetch the current
        price and compute reward. Then retrain if enough samples exist.
        """
        import yfinance as yf

        try:
            current_price = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
        except Exception as e:
            logger.warning(f"RL resolve: cannot fetch price for {ticker}: {e}")
            return

        cutoff = datetime.utcnow() - timedelta(days=3)
        updated = False

        for rec in self._records:
            if rec["ticker"] != ticker:
                continue
            if rec["outcome"] is not None:
                continue
            pred_time = datetime.fromisoformat(rec["predicted_at"])
            if pred_time > cutoff:
                continue

            price_then = rec["price_at_prediction"]
            price_change_pct = (
                (current_price - price_then) / (price_then + 1e-9) * 100
            )

            if price_change_pct > 0.5:
                actual = "UP"
            elif price_change_pct < -0.5:
                actual = "DOWN"
            else:
                actual = "NEUTRAL"

            predicted = rec["prediction"].get("direction", "NEUTRAL")
            if actual == "NEUTRAL":
                reward = 0.0
            elif predicted == actual:
                reward = 1.0
            else:
                reward = -1.0

            rec["outcome"] = actual
            rec["reward"] = reward
            rec["price_resolved"] = float(current_price)
            rec["price_change_pct"] = round(float(price_change_pct), 4)
            updated = True

        if updated:
            self.feedback_log.write_text(
                "\n".join(json.dumps(r) for r in self._records) + "\n"
            )
            logger.info(f"RL: Updated outcomes for {ticker}")
            self._maybe_retrain(ticker)

    # ─── retrain ──────────────────────────────────────────────────────────────

    def _maybe_retrain(self, ticker: str):
        labelled = [
            r for r in self._records
            if r["ticker"] == ticker
            and r.get("reward") is not None
            and r.get("reward") != 0.0
        ]
        if len(labelled) < 20:
            logger.info(
                f"RL: Only {len(labelled)} labelled samples for {ticker};"
                " skipping retrain."
            )
            return

        X = np.array([r["feature_vec"] for r in labelled], dtype=np.float32)
        y = np.array([1 if r["outcome"] == "UP" else 0 for r in labelled])

        sample_weights = np.array([
            max(0.5, r["prediction"].get("probability", 0.5))
            * (1.5 if r["reward"] == 1 else 0.5)
            for r in labelled
        ])

        predictor = StockPredictor(ticker)
        predictor.fit(X, y, sample_weight=sample_weights)
        logger.success(
            f"RL: Retrained model for {ticker} on {len(labelled)} samples."
        )

    # ─── stats ────────────────────────────────────────────────────────────────

    def get_stats(self, ticker: str) -> dict:
        resolved = [
            r for r in self._records
            if r["ticker"] == ticker and r.get("reward") is not None
        ]
        if not resolved:
            return {"accuracy": None, "total": 0, "correct": 0}
        correct = sum(1 for r in resolved if r["reward"] == 1.0)
        return {
            "accuracy": round(correct / len(resolved), 3),
            "total": len(resolved),
            "correct": correct,
            "recent_rewards": [r["reward"] for r in resolved[-10:]],
        }
