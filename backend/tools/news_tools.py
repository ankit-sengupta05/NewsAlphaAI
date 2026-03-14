"""
backend/tools/news_tools.py
LangGraph-compatible tools for news ingestion.
Each function is decorated with @tool for use inside graph nodes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

import requests
from langchain_core.tools import tool
from loguru import logger

from backend.core.config import settings


def _save_raw_news(articles: list[dict], ticker: str):
    """Persist raw news JSON to news_data_dir/{ticker}/."""
    dest = settings.news_data_dir / ticker
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    (dest / f"raw_{stamp}.json").write_text(
        json.dumps(articles, indent=2, default=str)
    )


@tool
def fetch_news_newsapi(ticker: str) -> list[dict]:
    """
    Fetch recent financial news for a stock ticker using NewsAPI.
    Returns a list of article dicts with title, description, url, publishedAt.
    """
    if not settings.newsapi_key:
        logger.warning("NEWSAPI_KEY not set, skipping NewsAPI.")
        return []

    query = f"{ticker} stock"
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": settings.newsapi_key,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "from": (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d"),
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
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
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        return []


@tool
def fetch_news_gnews(ticker: str) -> list[dict]:
    """
    Fetch recent financial news via GNews free API.
    """
    if not settings.gnews_api_key:
        logger.warning("GNEWS_API_KEY not set, skipping GNews.")
        return []

    url = "https://gnews.io/api/v4/search"
    params = {
        "q": f"{ticker} stock market",
        "token": settings.gnews_api_key,
        "lang": "en",
        "max": 10,
        "sortby": "publishedAt",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
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
    except Exception as e:
        logger.error(f"GNews error: {e}")
        return []


@tool
def fetch_news_alphavantage(ticker: str) -> list[dict]:
    """
    Fetch news + pre-computed sentiment from AlphaVantage News Sentiment API.
    """
    if not settings.alphavantage_key:
        return []

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": settings.alphavantage_key,
        "limit": 20,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        feed = resp.json().get("feed", [])
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
                "av_sentiment_score": float(ts.get("ticker_sentiment_score", 0)),
            })
        _save_raw_news(results, ticker)
        return results
    except Exception as e:
        logger.error(f"AlphaVantage news error: {e}")
        return []


def merge_and_deduplicate(news_lists: list[list[dict]]) -> list[dict]:
    """Merge multiple source lists, deduplicate by article id."""
    seen = set()
    merged = []
    for lst in news_lists:
        for article in lst:
            aid = article.get("id", "")
            if aid not in seen:
                seen.add(aid)
                merged.append(article)
    return merged
