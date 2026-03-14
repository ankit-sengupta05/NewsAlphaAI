"""
backend/tools/news_tools.py
LangGraph-compatible tools for news ingestion.
Each function is decorated with @tool for use inside graph nodes.
"""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timedelta

import requests
from langchain_core.tools import tool
from loguru import logger

from backend.core.config import settings


# Single shared session with connection pooling + aggressive timeouts
_session = requests.Session()
_session.headers.update({"User-Agent": "NewsAlphaAI/1.0"})

# Per-source timeout in seconds
_TIMEOUT = (5, 10)  # (connect timeout, read timeout)

# Executor for running blocking requests without blocking the event loop
_executor = ThreadPoolExecutor(max_workers=4)


def _save_raw_news(articles: list[dict], ticker: str):
    """Persist raw news JSON to news_data_dir/{ticker}/."""
    try:
        dest = settings.news_data_dir / ticker
        dest.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        (dest / f"raw_{stamp}.json").write_text(
            json.dumps(articles, indent=2, default=str)
        )
    except Exception as e:
        logger.warning(f"Could not save raw news for {ticker}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  Individual fetchers (plain functions, not tools — called concurrently)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_newsapi(ticker: str) -> list[dict]:
    if not settings.newsapi_key:
        logger.warning("NEWSAPI_KEY not set, skipping NewsAPI.")
        return []

    logger.info(f"[{ticker}] NewsAPI: starting fetch...")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f"{ticker} stock",
        "apiKey": settings.newsapi_key,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "from": (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d"),
    }
    try:
        resp = _session.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        logger.info(f"[{ticker}] NewsAPI: got {len(articles)} articles.")
        _save_raw_news(articles, ticker)
        return [
            {
                "id": hashlib.md5(a.get("url", "").encode()).hexdigest()[:12],
                "source": "newsapi",
                "ticker": ticker,
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "content": a.get("content", ""),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
            }
            for a in articles
            if a.get("title")
        ]
    except requests.exceptions.Timeout:
        logger.error(f"[{ticker}] NewsAPI: TIMED OUT after {_TIMEOUT}s")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[{ticker}] NewsAPI: connection error: {e}")
        return []
    except Exception as e:
        logger.error(f"[{ticker}] NewsAPI error: {e}")
        return []


def _fetch_gnews(ticker: str) -> list[dict]:
    if not settings.gnews_api_key:
        logger.warning("GNEWS_API_KEY not set, skipping GNews.")
        return []

    logger.info(f"[{ticker}] GNews: starting fetch...")
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": f"{ticker} stock market",
        "token": settings.gnews_api_key,
        "lang": "en",
        "max": 10,
        "sortby": "publishedAt",
    }
    try:
        resp = _session.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        logger.info(f"[{ticker}] GNews: got {len(articles)} articles.")
        _save_raw_news(articles, ticker)
        return [
            {
                "id": hashlib.md5(a.get("url", "").encode()).hexdigest()[:12],
                "source": "gnews",
                "ticker": ticker,
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "content": a.get("content", ""),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
            }
            for a in articles
            if a.get("title")
        ]
    except requests.exceptions.Timeout:
        logger.error(f"[{ticker}] GNews: TIMED OUT after {_TIMEOUT}s")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[{ticker}] GNews: connection error: {e}")
        return []
    except Exception as e:
        logger.error(f"[{ticker}] GNews error: {e}")
        return []


def _fetch_alphavantage(ticker: str) -> list[dict]:
    if not settings.alphavantage_key:
        logger.warning("ALPHAVANTAGE_KEY not set, skipping AlphaVantage.")
        return []

    logger.info(f"[{ticker}] AlphaVantage: starting fetch...")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": settings.alphavantage_key,
        "limit": 20,
    }
    try:
        resp = _session.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # AlphaVantage returns error messages in JSON body instead of HTTP codes
        if "Information" in data or "Note" in data:
            msg = data.get("Information") or data.get("Note", "")
            logger.warning(f"[{ticker}] AlphaVantage rate limit / info: {msg}")
            return []

        feed = data.get("feed", [])
        logger.info(f"[{ticker}] AlphaVantage: got {len(feed)} articles.")
        results = []
        for a in feed:
            ticker_sentiments = {
                t["ticker"]: t for t in a.get("ticker_sentiment", [])
            }
            ts = ticker_sentiments.get(ticker, {})
            results.append({
                "id": hashlib.md5(a.get("url", "").encode()).hexdigest()[:12],
                "source": "alphavantage",
                "ticker": ticker,
                "title": a.get("title", ""),
                "description": a.get("summary", ""),
                "content": a.get("summary", ""),
                "url": a.get("url", ""),
                "published_at": a.get("time_published", ""),
                "av_sentiment_label": ts.get("ticker_sentiment_label", ""),
                "av_sentiment_score": float(
                    ts.get("ticker_sentiment_score", 0)
                ),
            })
        _save_raw_news(results, ticker)
        return results
    except requests.exceptions.Timeout:
        logger.error(f"[{ticker}] AlphaVantage: TIMED OUT after {_TIMEOUT}s")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[{ticker}] AlphaVantage: connection error: {e}")
        return []
    except Exception as e:
        logger.error(f"[{ticker}] AlphaVantage error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
#  LangGraph @tool wrappers — fetch all 3 sources concurrently
# ─────────────────────────────────────────────────────────────────────────────

@tool
def fetch_news_newsapi(ticker: str) -> list[dict]:
    """Fetch recent financial news for a stock ticker using NewsAPI."""
    return _fetch_newsapi(ticker)


@tool
def fetch_news_gnews(ticker: str) -> list[dict]:
    """Fetch recent financial news via GNews free API."""
    return _fetch_gnews(ticker)


@tool
def fetch_news_alphavantage(ticker: str) -> list[dict]:
    """Fetch news + pre-computed sentiment from AlphaVantage News Sentiment API."""
    return _fetch_alphavantage(ticker)


# ─────────────────────────────────────────────────────────────────────────────
#  Merge helper — also used directly by node_fetch_news
# ─────────────────────────────────────────────────────────────────────────────

def merge_and_deduplicate(news_lists: list[list[dict]]) -> list[dict]:
    """Merge multiple source lists, deduplicate by article id."""
    seen: set[str] = set()
    merged: list[dict] = []
    for lst in news_lists:
        for article in lst:
            aid = article.get("id", "")
            if aid not in seen:
                seen.add(aid)
                merged.append(article)
    logger.info(f"Merged {len(merged)} unique articles from {len(news_lists)} sources.")
    return merged


# ─────────────────────────────────────────────────────────────────────────────
#  Concurrent fetch helper — call all 3 sources in parallel with hard timeout
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all_news(ticker: str, max_wait: float = 20.0) -> list[dict]:
    """
    Fetch from all 3 sources concurrently using a thread pool.
    Each source has its own connect+read timeout (_TIMEOUT).
    The overall call is capped at max_wait seconds.
    Falls back gracefully if any source fails or times out.
    """
    fetchers = [_fetch_newsapi, _fetch_gnews, _fetch_alphavantage]
    results: list[list[dict]] = [[], [], []]

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn, ticker): i for i, fn in enumerate(fetchers)}
        for future in futures:
            idx = futures[future]
            try:
                results[idx] = future.result(timeout=max_wait)
            except FuturesTimeoutError:
                name = fetchers[idx].__name__
                logger.error(
                    f"[{ticker}] {name}: hard timeout after {max_wait}s — skipping"
                )
            except Exception as e:
                name = fetchers[idx].__name__
                logger.error(f"[{ticker}] {name}: unexpected error: {e}")

    return merge_and_deduplicate(results)
