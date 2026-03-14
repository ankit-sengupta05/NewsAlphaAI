"""
backend/tools/sentiment_tools.py
LLM-powered sentiment & impact analysis on financial news.
"""
from __future__ import annotations

import json
import re

from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from loguru import logger

from backend.models_registry.llm_registry import get_llm


SENTIMENT_PROMPT = PromptTemplate.from_template(
    """You are a financial analyst AI. Analyse the following news article about {ticker} stock.

Article:
{text}

Respond ONLY with a valid JSON object (no markdown, no preamble) with these keys:
- sentiment: "BULLISH" | "BEARISH" | "NEUTRAL"
- confidence: float 0.0-1.0
- impact_score: float -1.0 (very negative) to 1.0 (very positive)
- key_events: list of up to 3 short strings describing key events
- reasoning: one sentence explaining your assessment
"""
)

BATCH_SENTIMENT_PROMPT = PromptTemplate.from_template(
    "You are a senior financial analyst. "
    "You are given multiple news headlines and summaries about {ticker}.\n"
    "\nNews items:\n{news_block}\n"
    "\nBased on ALL items collectively, respond ONLY with a valid JSON object:\n"
    "- overall_sentiment: \"BULLISH\" | \"BEARISH\" | \"NEUTRAL\"\n"
    "- sentiment_score: float -1.0 to 1.0\n"
    "- confidence: float 0.0-1.0\n"
    "- dominant_themes: list of up to 4 theme strings\n"
    "- risk_factors: list of up to 3 short strings\n"
    "- catalysts: list of up to 3 bullish catalysts\n"
    "- summary: 2-3 sentence market narrative\n"
)


def _parse_json_response(text: str) -> dict:
    """Robustly extract JSON from LLM response."""
    text = re.sub(r"```json|```", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


@tool
def analyse_single_article(article: dict) -> dict:
    """
    Run LLM sentiment analysis on a single news article.
    Returns enriched article dict with sentiment fields added.
    """
    ticker = article.get("ticker", "UNKNOWN")
    text = (
        f"{article.get('title', '')}. "
        f"{article.get('description', '')} "
        f"{article.get('content', '')}"
    ).strip()
    if len(text) < 20:
        return {
            **article,
            "sentiment": "NEUTRAL",
            "impact_score": 0.0,
            "confidence": 0.0,
        }

    llm = get_llm()
    prompt = SENTIMENT_PROMPT.format(ticker=ticker, text=text[:1200])
    try:
        response = llm.invoke(prompt)
        if hasattr(response, "content"):
            response = response.content
        parsed = _parse_json_response(str(response))
        return {**article, **parsed}
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return {
            **article,
            "sentiment": "NEUTRAL",
            "impact_score": 0.0,
            "confidence": 0.0,
        }


@tool
def analyse_news_batch(ticker: str, articles: list[dict]) -> dict:
    """
    Holistic sentiment analysis across all fetched articles for a ticker.
    Returns aggregate market narrative dict.
    """
    if not articles:
        return {
            "overall_sentiment": "NEUTRAL",
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "dominant_themes": [],
            "risk_factors": [],
            "catalysts": [],
            "summary": "No news available.",
        }

    news_block = "\n".join(
        f"{i+1}. [{a.get('published_at', '')[:10]}] "
        f"{a.get('title', '')} — {a.get('description', '')[:150]}"
        for i, a in enumerate(articles[:15])
    )

    llm = get_llm()
    prompt = BATCH_SENTIMENT_PROMPT.format(ticker=ticker, news_block=news_block)
    try:
        response = llm.invoke(prompt)
        if hasattr(response, "content"):
            response = response.content
        parsed = _parse_json_response(str(response))
        if parsed:
            return parsed
    except Exception as e:
        logger.error(f"Batch sentiment error: {e}")

    return {
        "overall_sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "confidence": 0.3,
        "dominant_themes": [],
        "risk_factors": [],
        "catalysts": [],
        "summary": "Analysis unavailable.",
    }
