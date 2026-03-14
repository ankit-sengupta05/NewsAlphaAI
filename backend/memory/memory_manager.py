"""
backend/memory/memory_manager.py
Agent long-term memory stored in a SEPARATE directory (settings.memory_dir).
Uses LangChain's ConversationSummaryBufferMemory + JSON persistence.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any


from backend.core.config import settings


class AgentMemoryManager:
    """
    Persists agent interaction history and stock prediction context
    independently from news/stock raw data.
    """

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.memory_path = settings.memory_dir / f"{self.ticker}_memory.json"
        self._data: dict[str, Any] = self._load()

    # ─── persistence ─────────────────────────────────────────────────────────

    def _load(self) -> dict[str, Any]:
        if self.memory_path.exists():
            return json.loads(self.memory_path.read_text())
        return {"interactions": [], "prediction_history": [], "context_summary": ""}

    def _save(self):
        self.memory_path.write_text(json.dumps(self._data, indent=2, default=str))

    # ─── interactions ─────────────────────────────────────────────────────────

    def add_interaction(self, role: str, content: str):
        self._data["interactions"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep last 50 interactions to avoid bloat
        self._data["interactions"] = self._data["interactions"][-50:]
        self._save()

    def get_recent_interactions(self, n: int = 10) -> list[dict]:
        return self._data["interactions"][-n:]

    # ─── prediction history ───────────────────────────────────────────────────

    def add_prediction(self, prediction: dict):
        """Store a prediction record with outcome for RL feedback."""
        prediction["timestamp"] = datetime.utcnow().isoformat()
        self._data["prediction_history"].append(prediction)
        self._data["prediction_history"] = self._data["prediction_history"][-200:]
        self._save()

    def get_prediction_history(self) -> list[dict]:
        return self._data["prediction_history"]

    # ─── context summary ──────────────────────────────────────────────────────

    def update_summary(self, summary: str):
        self._data["context_summary"] = summary
        self._save()

    def get_summary(self) -> str:
        return self._data.get("context_summary", "")

    # ─── helper ──────────────────────────────────────────────────────────────

    def format_context_for_prompt(self) -> str:
        summary = self.get_summary()
        recent = self.get_recent_interactions(5)
        lines = []
        if summary:
            lines.append(f"[Memory Summary]\n{summary}\n")
        if recent:
            lines.append("[Recent Interactions]")
            for item in recent:
                lines.append(f"  {item['role']}: {item['content'][:200]}")
        return "\n".join(lines)
