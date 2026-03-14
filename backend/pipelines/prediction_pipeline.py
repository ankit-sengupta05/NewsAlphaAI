"""
backend/pipelines/prediction_pipeline.py
LangGraph orchestration of the full NewsAlphaAI prediction workflow.

Graph:
  fetch_news -> analyse_sentiment -> embed_store -> fetch_stock ->
  rag_retrieve -> llm_reason -> ml_predict -> final_predict -> DONE
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict, Annotated
import operator

from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from loguru import logger

# ─────────────────────────────────────────────────────────────────────────────
#  Graph State
# ─────────────────────────────────────────────────────────────────────────────


class PipelineState(TypedDict):
    ticker: str
    raw_articles: list[dict]
    analysed_articles: list[dict]
    batch_sentiment: dict
    stock_info: dict
    tech_features: dict
    rag_docs: list[dict]
    llm_reasoning: str
    ml_prediction: dict
    final_prediction: dict
    errors: Annotated[list[str], operator.add]
    logs: Annotated[list[str], operator.add]
    started_at: str


# ─────────────────────────────────────────────────────────────────────────────
#  Node implementations
# ─────────────────────────────────────────────────────────────────────────────

def node_fetch_news(state: PipelineState) -> PipelineState:
    from backend.tools.news_tools import (
        fetch_news_newsapi, fetch_news_gnews,
        fetch_news_alphavantage, merge_and_deduplicate,
    )
    ticker = state["ticker"]
    logger.info(f"[{ticker}] Fetching news...")
    lists = [
        fetch_news_newsapi.invoke({"ticker": ticker}),
        fetch_news_gnews.invoke({"ticker": ticker}),
        fetch_news_alphavantage.invoke({"ticker": ticker}),
    ]
    articles = merge_and_deduplicate(lists)
    return {
        **state,
        "raw_articles": articles,
        "logs": [f"Fetched {len(articles)} articles from {len(lists)} sources"],
    }


def node_analyse_sentiment(state: PipelineState) -> PipelineState:
    from backend.tools.sentiment_tools import analyse_single_article, analyse_news_batch
    ticker = state["ticker"]
    articles = state.get("raw_articles", [])
    logger.info(f"[{ticker}] Analysing sentiment on {len(articles)} articles...")

    analysed = []
    for a in articles[:10]:
        result = analyse_single_article.invoke({"article": a})
        analysed.append(result)

    batch = analyse_news_batch.invoke({"ticker": ticker, "articles": articles})

    sentiment = batch.get('overall_sentiment')
    score = batch.get('sentiment_score', 0)
    return {
        **state,
        "analysed_articles": analysed,
        "batch_sentiment": batch,
        "logs": [f"Sentiment: {sentiment} (score={score:.2f})"],
    }


def node_embed_store(state: PipelineState) -> PipelineState:
    from backend.tools.embedding_tools import embed_and_store_articles
    articles = (
        state.get("analysed_articles", [])
        or state.get("raw_articles", [])
    )
    result = embed_and_store_articles.invoke({"articles": articles})
    return {
        **state,
        "logs": [f"Embedded and stored {result.get('stored', 0)} articles"],
    }


def node_fetch_stock(state: PipelineState) -> PipelineState:
    from backend.tools.stock_tools import (
        get_stock_info,
        compute_technical_features,
    )
    ticker = state["ticker"]
    logger.info(f"[{ticker}] Fetching stock data...")
    stock_info = get_stock_info.invoke({"ticker": ticker})
    tech_features = compute_technical_features.invoke({"ticker": ticker})
    return {
        **state,
        "stock_info": stock_info,
        "tech_features": tech_features,
        "logs": [f"Fetched stock data for {ticker}"],
    }


def node_rag_retrieve(state: PipelineState) -> PipelineState:
    from backend.tools.embedding_tools import rag_retrieve_news
    ticker = state["ticker"]
    batch = state.get("batch_sentiment", {})
    themes = " ".join(batch.get("dominant_themes", ["earnings", "market outlook"]))
    query = f"{ticker} stock price movement {themes}"
    docs = rag_retrieve_news.invoke({"ticker": ticker, "query": query, "k": 6})
    return {
        **state,
        "rag_docs": docs,
        "logs": [f"RAG retrieved {len(docs)} relevant documents"],
    }


REASONING_PROMPT = PromptTemplate.from_template(
    """You are an expert quantitative analyst and stock prediction AI.

TASK: Predict whether {ticker} stock will go UP or DOWN in the next 2-3 trading days.

## Technical Indicators
{tech_features}

## News Sentiment Analysis
Overall: {overall_sentiment} (score: {sentiment_score})
Themes: {themes}
Catalysts: {catalysts}
Risk Factors: {risks}
Narrative: {narrative}

## Relevant News Context (RAG)
{rag_context}

## Memory Context
{memory_context}

Based on all of the above, provide:
1. Your directional prediction: UP or DOWN
2. Probability estimate (50-95%)
3. Key reasoning (3-5 bullet points)
4. Confidence level: HIGH / MEDIUM / LOW
5. Timeframe: 2-3 days

Format your response as:
DIRECTION: [UP/DOWN]
PROBABILITY: [XX%]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING:
- point 1
- point 2
- point 3
SUMMARY: [one sentence]
"""
)


def node_llm_reason(state: PipelineState) -> PipelineState:
    from backend.models_registry.llm_registry import get_llm
    from backend.memory.memory_manager import AgentMemoryManager

    ticker = state["ticker"]
    tech = state.get("tech_features", {})
    batch = state.get("batch_sentiment", {})
    rag_docs = state.get("rag_docs", [])
    memory_mgr = AgentMemoryManager(ticker)

    rag_context = "\n".join(
        f"- {d['content'][:200]}" for d in rag_docs[:5]
    ) or "No relevant context found."

    prompt = REASONING_PROMPT.format(
        ticker=ticker,
        tech_features=str(tech),
        overall_sentiment=batch.get("overall_sentiment", "NEUTRAL"),
        sentiment_score=batch.get("sentiment_score", 0.0),
        themes=", ".join(batch.get("dominant_themes", [])),
        catalysts=", ".join(batch.get("catalysts", [])),
        risks=", ".join(batch.get("risk_factors", [])),
        narrative=batch.get("summary", ""),
        rag_context=rag_context,
        memory_context=memory_mgr.format_context_for_prompt(),
    )

    llm = get_llm()
    try:
        response = llm.invoke(prompt)
        reasoning = (
            response.content if hasattr(response, "content") else str(response)
        )
    except Exception as e:
        logger.error(f"LLM reasoning error: {e}")
        reasoning = (
            "DIRECTION: NEUTRAL\nPROBABILITY: 50%\nCONFIDENCE: LOW\n"
            "REASONING:\n- Insufficient data\n"
            "SUMMARY: Cannot determine direction."
        )

    memory_mgr.add_interaction("assistant", reasoning[:500])

    return {
        **state,
        "llm_reasoning": reasoning,
        "logs": ["LLM reasoning complete"],
    }


def node_ml_predict(state: PipelineState) -> PipelineState:
    from backend.ml.prediction_model import StockPredictor

    ticker = state["ticker"]
    tech = state.get("tech_features", {})
    batch = state.get("batch_sentiment", {})
    analysed = state.get("analysed_articles", [])

    feature_vec = StockPredictor.build_feature_vector(tech, batch, analysed)
    predictor = StockPredictor(ticker)
    ml_pred = predictor.predict(feature_vec)

    return {
        **state,
        "ml_prediction": {
            **ml_pred,
            "feature_vec": feature_vec.flatten().tolist(),
        },
        "logs": [f"ML prediction: {ml_pred['direction']} ({ml_pred['probability']:.1%})"],
    }


def _parse_llm_direction(reasoning: str) -> tuple[str, float]:
    import re
    direction = "NEUTRAL"
    probability = 0.5
    for line in reasoning.splitlines():
        if line.startswith("DIRECTION:"):
            val = line.split(":", 1)[1].strip().upper()
            if "UP" in val:
                direction = "UP"
            elif "DOWN" in val:
                direction = "DOWN"
        if line.startswith("PROBABILITY:"):
            m = re.search(r"(\d+)", line)
            if m:
                probability = int(m.group(1)) / 100.0
    return direction, probability


def node_final_predict(state: PipelineState) -> PipelineState:
    from backend.memory.memory_manager import AgentMemoryManager
    from backend.rl.feedback_loop import RLFeedbackLoop

    ticker = state["ticker"]
    ml = state.get("ml_prediction", {})
    reasoning = state.get("llm_reasoning", "")
    batch = state.get("batch_sentiment", {})
    tech = state.get("tech_features", {})

    llm_dir, llm_prob = _parse_llm_direction(reasoning)
    ml_dir = ml.get("direction", "NEUTRAL")
    ml_prob = ml.get("probability", 0.5)

    llm_score = llm_prob if llm_dir == "UP" else (1 - llm_prob)
    ml_score = ml_prob if ml_dir == "UP" else (1 - ml_prob)
    ensemble_score = 0.6 * llm_score + 0.4 * ml_score

    direction = "UP" if ensemble_score > 0.5 else "DOWN"
    probability = max(ensemble_score, 1 - ensemble_score)
    confidence = (
        "HIGH" if probability > 0.72
        else "MEDIUM" if probability > 0.58
        else "LOW"
    )

    bullets = [
        line.strip()[2:].strip()
        for line in reasoning.splitlines()
        if line.strip().startswith("-")
    ]

    summary_line = ""
    for line in reasoning.splitlines():
        if line.startswith("SUMMARY:"):
            summary_line = line.split(":", 1)[1].strip()

    final = {
        "ticker": ticker,
        "direction": direction,
        "probability": round(probability, 4),
        "confidence": confidence,
        "llm_direction": llm_dir,
        "llm_probability": round(llm_prob, 4),
        "ml_direction": ml_dir,
        "ml_probability": round(ml_prob, 4),
        "sentiment": batch.get("overall_sentiment", "NEUTRAL"),
        "sentiment_score": batch.get("sentiment_score", 0.0),
        "price": tech.get("price"),
        "rsi": tech.get("rsi"),
        "macd": tech.get("macd"),
        "reasoning_bullets": bullets,
        "summary": summary_line,
        "timestamp": datetime.utcnow().isoformat(),
    }

    memory_mgr = AgentMemoryManager(ticker)
    memory_mgr.add_prediction(final)

    rl = RLFeedbackLoop()
    rl.record_prediction(
        ticker=ticker,
        prediction={"direction": direction, "probability": probability},
        feature_vec=ml.get("feature_vec", []),
        price_at_prediction=tech.get("price", 0.0),
    )
    rl.resolve_outcomes(ticker)

    return {
        **state,
        "final_prediction": final,
        "logs": [f"Final prediction: {direction} @ {probability:.1%} ({confidence})"],
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Build the LangGraph
# ─────────────────────────────────────────────────────────────────────────────

def build_pipeline() -> Any:
    g = StateGraph(PipelineState)
    g.add_node("fetch_news", node_fetch_news)
    g.add_node("analyse_sentiment", node_analyse_sentiment)
    g.add_node("embed_store", node_embed_store)
    g.add_node("fetch_stock", node_fetch_stock)
    g.add_node("rag_retrieve", node_rag_retrieve)
    g.add_node("llm_reason", node_llm_reason)
    g.add_node("ml_predict", node_ml_predict)
    g.add_node("final_predict", node_final_predict)

    g.set_entry_point("fetch_news")
    g.add_edge("fetch_news", "analyse_sentiment")
    g.add_edge("analyse_sentiment", "embed_store")
    g.add_edge("embed_store", "fetch_stock")
    g.add_edge("fetch_stock", "rag_retrieve")
    g.add_edge("rag_retrieve", "llm_reason")
    g.add_edge("llm_reason", "ml_predict")
    g.add_edge("ml_predict", "final_predict")
    g.add_edge("final_predict", END)

    return g.compile()


_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


async def run_prediction(ticker: str, on_step=None) -> dict:
    """
    Run the full prediction pipeline for a ticker.
    on_step: async callable(step_name, state) for streaming updates.
    Compatible with LangGraph 1.x which streams dict chunks keyed by node name.
    """
    pipeline = get_pipeline()
    initial_state: PipelineState = {
        "ticker": ticker.upper(),
        "raw_articles": [],
        "analysed_articles": [],
        "batch_sentiment": {},
        "stock_info": {},
        "tech_features": {},
        "rag_docs": [],
        "llm_reasoning": "",
        "ml_prediction": {},
        "final_prediction": {},
        "errors": [],
        "logs": [],
        "started_at": datetime.utcnow().isoformat(),
    }

    final_state = initial_state

    async for chunk in pipeline.astream(initial_state, stream_mode="updates"):
        if isinstance(chunk, dict):
            for step_name, state_update in chunk.items():
                if isinstance(state_update, dict):
                    final_state = {**final_state, **state_update}
                if on_step:
                    await on_step(step_name, final_state)
        else:
            try:
                step_name, state_update = chunk
                if isinstance(state_update, dict):
                    final_state = {**final_state, **state_update}
                if on_step:
                    await on_step(step_name, final_state)
            except (TypeError, ValueError):
                pass

    return final_state
