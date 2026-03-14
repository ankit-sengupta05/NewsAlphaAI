"""
backend/tools/embedding_tools.py
Tools for embedding news articles and storing/retrieving from vector DB.
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.tools import tool
from loguru import logger

from backend.models_registry.vectordb_registry import get_vectorstore


@tool
def embed_and_store_articles(articles: list[dict]) -> dict:
    """
    Embed a list of news article dicts and upsert them into the vector store.
    Each article must have at minimum: id, ticker, title, description/content.
    Returns count of articles stored.
    """
    if not articles:
        return {"stored": 0}

    store = get_vectorstore("news")
    docs = []
    for a in articles:
        text = (
            f"{a.get('title', '')}. "
            f"{a.get('description', '')} "
            f"{a.get('content', '')}"
        ).strip()
        if not text or text == ".":
            continue
        docs.append(Document(
            page_content=text,
            metadata={
                "id": a.get("id", ""),
                "ticker": a.get("ticker", ""),
                "source": a.get("source", ""),
                "url": a.get("url", ""),
                "published_at": a.get("published_at", ""),
                "av_sentiment_label": a.get("av_sentiment_label", ""),
                "av_sentiment_score": a.get("av_sentiment_score", 0.0),
            }
        ))

    if not docs:
        return {"stored": 0}

    store.add_documents(docs)
    if hasattr(store, "_collection"):
        try:
            store.persist()
        except Exception:
            pass

    logger.info(f"Stored {len(docs)} articles in vector DB.")
    return {"stored": len(docs)}


@tool
def rag_retrieve_news(ticker: str, query: str, k: int = 6) -> list[dict]:
    """
    Retrieve the most relevant news documents for a ticker and query string.
    Used to feed context into the prediction LLM.
    """
    store = get_vectorstore("news")
    combined_query = f"{ticker} {query}"
    try:
        docs = store.similarity_search(
            combined_query, k=k,
            filter={"ticker": ticker},
        )
    except Exception:
        docs = store.similarity_search(combined_query, k=k)

    return [
        {"content": d.page_content, "metadata": d.metadata}
        for d in docs
    ]
