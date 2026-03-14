"""
backend/api/main.py
FastAPI application with REST endpoints + WebSocket for real-time pipeline streaming.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.core.config import settings
from backend.api.lifespan import lifespan
from backend.pipelines.prediction_pipeline import run_prediction
from backend.rl.feedback_loop import RLFeedbackLoop
from backend.memory.memory_manager import AgentMemoryManager
from backend.tools.stock_tools import get_stock_info, compute_technical_features, fetch_stock_ohlcv


app = FastAPI(
    title="NewsAlphaAI API",
    description="AI-powered stock prediction via news analysis + LLM + RL",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
#  REST Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/stock/{ticker}/info")
async def stock_info(ticker: str):
    """Basic company info."""
    info = get_stock_info.invoke({"ticker": ticker.upper()})
    return info


@app.get("/api/stock/{ticker}/chart")
async def stock_chart(ticker: str, period: str = "30d"):
    """OHLCV data for chart rendering."""
    data = fetch_stock_ohlcv.invoke({"ticker": ticker.upper(), "period": period})
    return data


@app.get("/api/stock/{ticker}/technicals")
async def stock_technicals(ticker: str):
    """Technical indicator snapshot."""
    return compute_technical_features.invoke({"ticker": ticker.upper()})


@app.get("/api/prediction/{ticker}/history")
async def prediction_history(ticker: str):
    """Return historical predictions from memory."""
    mgr = AgentMemoryManager(ticker.upper())
    return {"ticker": ticker.upper(), "history": mgr.get_prediction_history()}


@app.get("/api/prediction/{ticker}/rl-stats")
async def rl_stats(ticker: str):
    """RL model accuracy stats."""
    rl = RLFeedbackLoop()
    return rl.get_stats(ticker.upper())


@app.post("/api/predict/{ticker}")
async def predict_rest(ticker: str):
    """
    Run full prediction pipeline synchronously (blocking).
    For real-time streaming, use the WebSocket endpoint instead.
    """
    try:
        state = await run_prediction(ticker.upper())
        return state.get("final_prediction", {})
    except Exception as e:
        logger.error(f"Prediction error for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
#  WebSocket – Real-time pipeline streaming
# ─────────────────────────────────────────────────────────────────────────────

STEP_LABELS = {
    "fetch_news": "📰 Fetching news articles…",
    "analyse_sentiment": "🧠 Analysing sentiment with LLM…",
    "embed_store": "🔢 Embedding & storing in vector DB…",
    "fetch_stock": "📈 Fetching stock data & technicals…",
    "rag_retrieve": "🔍 RAG retrieval from vector store…",
    "llm_reason": "💡 LLM reasoning about price direction…",
    "ml_predict": "⚙️  ML model prediction…",
    "final_predict": "✅ Generating final ensemble prediction…",
}


@app.websocket("/ws/predict/{ticker}")
async def ws_predict(websocket: WebSocket, ticker: str):
    """
    WebSocket endpoint that streams pipeline progress to the frontend.
    Messages are JSON with: { type, step, label, data, logs }
    """
    await websocket.accept()
    ticker = ticker.upper()
    logger.info(f"WS: prediction started for {ticker}")

    try:
        await websocket.send_json({
            "type": "start",
            "ticker": ticker,
            "message": f"Starting prediction pipeline for {ticker}",
            "timestamp": datetime.utcnow().isoformat(),
        })

        async def on_step(step_name: str, state: dict):
            label = STEP_LABELS.get(step_name, step_name)
            logs = state.get("logs", [])
            payload = {
                "type": "step",
                "step": step_name,
                "label": label,
                "logs": logs[-3:],
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Include partial results if available
            if step_name == "fetch_news":
                payload["article_count"] = len(state.get("raw_articles", []))
            elif step_name == "analyse_sentiment":
                payload["sentiment"] = state.get("batch_sentiment", {})
            elif step_name == "fetch_stock":
                payload["technicals"] = state.get("tech_features", {})
            elif step_name == "final_predict":
                payload["prediction"] = state.get("final_prediction", {})
            try:
                await websocket.send_json(payload)
            except Exception:
                pass

        final_state = await run_prediction(ticker, on_step=on_step)

        await websocket.send_json({
            "type": "complete",
            "ticker": ticker,
            "prediction": final_state.get("final_prediction", {}),
            "timestamp": datetime.utcnow().isoformat(),
        })

    except WebSocketDisconnect:
        logger.info(f"WS: client disconnected for {ticker}")
    except Exception as e:
        logger.error(f"WS error for {ticker}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  WebSocket – Live market ticker broadcast (price updates)
# ─────────────────────────────────────────────────────────────────────────────

_price_subscribers: dict[str, list[WebSocket]] = {}


@app.websocket("/ws/live/{ticker}")
async def ws_live_price(websocket: WebSocket, ticker: str):
    """
    Broadcasts price updates every 15s for the given ticker.
    Multiple clients can subscribe to the same ticker.
    """
    await websocket.accept()
    ticker = ticker.upper()
    _price_subscribers.setdefault(ticker, []).append(websocket)

    try:
        import yfinance as yf
        while True:
            try:
                hist = yf.Ticker(ticker).history(period="2d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
                    change = price - prev
                    change_pct = change / (prev + 1e-9) * 100
                    await websocket.send_json({
                        "type": "price",
                        "ticker": ticker,
                        "price": round(price, 4),
                        "change": round(change, 4),
                        "change_pct": round(change_pct, 4),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        pass
    finally:
        if ticker in _price_subscribers:
            _price_subscribers[ticker] = [
                ws for ws in _price_subscribers[ticker] if ws != websocket
            ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
