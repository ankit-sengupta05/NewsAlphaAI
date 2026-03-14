"""
backend/api/lifespan.py
FastAPI lifespan context manager – starts/stops the APScheduler.
Import and attach to the FastAPI app in main.py.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from loguru import logger
from fastapi import FastAPI

from backend.utils.scheduler import create_scheduler

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    logger.info("Starting background scheduler…")
    _scheduler = create_scheduler()
    _scheduler.start()
    yield
    logger.info("Shutting down scheduler…")
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
