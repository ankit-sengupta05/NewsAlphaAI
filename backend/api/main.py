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
from backend.tools.stock_tools import (
    get_stock_info,
    compute_technical_features,
    fetch_stock_ohlcv,
)


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
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _safe_send(websocket: WebSocket, payload: dict) -> bool:
    """Send JSON safely. Returns False if the socket is already closed."""
    try:
        await websocket.send_json(payload)
        return True
    except (WebSocketDisconnect, RuntimeError):
        return False
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  REST Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/stock/{ticker}/info")
async def stock_info(ticker: str):
    """Basic company info."""
    return get_stock_info.invoke({"ticker": ticker.upper()})


@app.get("/api/stock/{ticker}/chart")
async def stock_chart(ticker: str, period: str = "30d"):
    """OHLCV data for chart rendering."""
    return fetch_stock_ohlcv.invoke({"ticker": ticker.upper(), "period": period})


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
    "fetch_news":        "Fetching news articles...",
    "analyse_sentiment": "Analysing sentiment with LLM...",
    "embed_store":       "Embedding and storing in vector DB...",
    "fetch_stock":       "Fetching stock data and technicals...",
    "rag_retrieve":      "RAG retrieval from vector store...",
    "llm_reason":        "LLM reasoning about price direction...",
    "ml_predict":        "ML model prediction...",
    "final_predict":     "Generating final ensemble prediction...",
}


@app.websocket("/ws/predict/{ticker}")
async def ws_predict(websocket: WebSocket, ticker: str):
    """
    WebSocket endpoint that streams pipeline progress to the frontend.
    Message types:
      start       — pipeline is starting
      step_start  — a node just began executing
      step        — a node just finished executing
      complete    — all nodes done, final prediction attached
      error       — something went wrong
    """
    await websocket.accept()
    ticker = ticker.upper()
    logger.info(f"WS predict: connected for {ticker}")
    connected = True

    try:
        sent = await _safe_send(websocket, {
            "type": "start",
            "ticker": ticker,
            "message": f"Starting prediction pipeline for {ticker}",
            "timestamp": datetime.utcnow().isoformat(),
        })
        if not sent:
            return

        async def on_step(step_name: str, state: dict):
            if not connected:
                return

            # __start__X  →  node just began, send step_start
            if step_name.startswith("__start__"):
                actual = step_name.replace("__start__", "")
                await _safe_send(websocket, {
                    "type": "step_start",
                    "step": actual,
                    "label": STEP_LABELS.get(actual, actual),
                    "logs": state.get("logs", [])[-2:],
                    "timestamp": datetime.utcnow().isoformat(),
                })
                return

            # Regular name  →  node just finished, send step
            payload = {
                "type": "step",
                "step": step_name,
                "label": STEP_LABELS.get(step_name, step_name),
                "logs": state.get("logs", [])[-3:],
                "timestamp": datetime.utcnow().isoformat(),
            }
            if step_name == "fetch_news":
                payload["article_count"] = len(state.get("raw_articles", []))
            elif step_name == "analyse_sentiment":
                payload["sentiment"] = state.get("batch_sentiment", {})
            elif step_name == "fetch_stock":
                payload["technicals"] = state.get("tech_features", {})
            elif step_name == "final_predict":
                payload["prediction"] = state.get("final_prediction", {})

            await _safe_send(websocket, payload)

        final_state = await run_prediction(ticker, on_step=on_step)

        await _safe_send(websocket, {
            "type": "complete",
            "ticker": ticker,
            "prediction": final_state.get("final_prediction", {}),
            "timestamp": datetime.utcnow().isoformat(),
        })

    except WebSocketDisconnect:
        logger.info(f"WS predict: client disconnected for {ticker}")
    except Exception as e:
        logger.error(f"WS predict error for {ticker}: {e}")
        await _safe_send(websocket, {"type": "error", "message": str(e)})
    finally:
        connected = False
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"WS predict: closed for {ticker}")


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
    logger.info(f"WS live: connected for {ticker}")

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
                    sent = await _safe_send(websocket, {
                        "type": "price",
                        "ticker": ticker,
                        "price": round(price, 4),
                        "change": round(change, 4),
                        "change_pct": round(change_pct, 4),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    if not sent:
                        break
            except (WebSocketDisconnect, RuntimeError):
                break
            except Exception as e:
                logger.warning(f"WS live price fetch error for {ticker}: {e}")
                sent = await _safe_send(websocket, {
                    "type": "error",
                    "message": str(e),
                })
                if not sent:
                    break

            await asyncio.sleep(15)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS live unexpected error for {ticker}: {e}")
    finally:
        if ticker in _price_subscribers:
            _price_subscribers[ticker] = [
                ws for ws in _price_subscribers[ticker] if ws != websocket
            ]
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"WS live: closed for {ticker}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
