"""
backend/utils/scheduler.py
APScheduler-based background job that runs prediction pipelines
on a watchlist at configurable intervals.
"""
from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from backend.pipelines.prediction_pipeline import run_prediction
from backend.rl.feedback_loop import RLFeedbackLoop

DEFAULT_WATCHLIST = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]


async def _run_watchlist(tickers: list[str]):
    logger.info(f"Scheduler: running prediction for {tickers}")
    rl = RLFeedbackLoop()
    for ticker in tickers:
        try:
            await run_prediction(ticker)
            rl.resolve_outcomes(ticker)
        except Exception as e:
            logger.error(f"Scheduler error for {ticker}: {e}")


def create_scheduler(
    watchlist: list[str] | None = None,
    interval_hours: int = 4,
) -> AsyncIOScheduler:
    """Create and return a configured APScheduler instance."""
    tickers = watchlist or DEFAULT_WATCHLIST
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _run_watchlist,
        "interval",
        hours=interval_hours,
        args=[tickers],
        next_run_time=datetime.now(),
        id="watchlist_prediction",
        replace_existing=True,
    )
    return scheduler
