# 🧠📈 NewsAlphaAI

> **AI-powered stock direction prediction** using real-time news, LLM reasoning,
> RAG pipelines, LangGraph orchestration, and reinforcement learning feedback.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML_Model-FF6600?style=for-the-badge)](https://xgboost.readthedocs.io)
[![LangSmith](https://img.shields.io/badge/LangSmith-Tracing-F0B429?style=for-the-badge)](https://smith.langchain.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

---

## �� Architecture

```
┌──────────────────────────────────────────────────────────────────�
│                        NEWS SOURCES                              │
│         NewsAPI  ·  GNews  ·  AlphaVantage                      │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────�
│               LANGGRAPH PIPELINE  (8 nodes)                      │
│                                                                  │
│  fetch_news → analyse_sentiment → embed_store → fetch_stock     │
│      → rag_retrieve → llm_reason → ml_predict → final_predict   │
│                                                                  │
│    [Gemma-3-4B-IT LLM]  +  [ChromaDB RAG]  +  [XGBoost ML]     │
└───────────────────────┬──────────────────────────────────────────┘
                        │
           ┌────────────┴─────────────�
           ▼                          ▼
 ┌──────────────────�      ┌──────────────────────�
 │  FastAPI Backend │      │   React Frontend      │
 │  REST + WebSocket│─────▶│   Upstox-style UI     │
 └──────────────────┘      └──────────────────────┘
           │
           ▼
 ┌──────────────────────────────────────────────�
 │           RL FEEDBACK LOOP                   │
 │  Record → Resolve → Reward → Retrain         │
 │              XGBoost Model                   │
 └──────────────────────────────────────────────┘
```

---

## ⚡ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| 🤖 **LLM** | Gemma-3-4B-IT (local HuggingFace) | News reasoning & direction prediction |
| 🔗 **Orchestration** | LangGraph + LangChain | 8-node prediction pipeline |
| � **Observability** | LangSmith | Pipeline tracing & debugging |
| 🗄� **Vector DB** | ChromaDB / FAISS | RAG news retrieval |
| 🧮 **Embeddings** | sentence-transformers `all-MiniLM-L6-v2` | Article embedding |
| 📊 **ML Model** | XGBoost + scikit-learn | Binary direction classifier |
| 🔄 **RL Feedback** | Custom policy-gradient loop | Auto-retraining on outcomes |
| 🚀 **Backend** | FastAPI + WebSockets + APScheduler | API + real-time streaming |
| 🎨 **Frontend** | React + Vite + TailwindCSS + lightweight-charts | Trading UI |

---

## � Project Structure

```
NewsAlphaAI/
├── 📄 .env.example
├── � backend/
│   ├── api/
│   │   ├── main.py                  � FastAPI app + WebSocket endpoints
│   │   └── lifespan.py              � APScheduler background jobs
│   ├── core/config.py               � Pydantic-settings config
│   ├── models_registry/
│   │   ├── llm_registry.py          � Modular LLM loader
│   │   └── vectordb_registry.py     � Chroma/FAISS factory
│   ├── memory/memory_manager.py     � Agent long-term memory
│   ├── tools/
│   │   ├── news_tools.py            � NewsAPI / GNews / AlphaVantage
│   │   ├── stock_tools.py           � yfinance + technical indicators
│   │   ├── embedding_tools.py       � Embed + store / RAG retrieve
│   │   └── sentiment_tools.py       � LLM sentiment analysis
│   ├── pipelines/prediction_pipeline.py  � Full LangGraph pipeline
│   ├── ml/prediction_model.py       � XGBoost binary classifier
│   ├── rl/feedback_loop.py          � RL outcome tracking + retrain
│   └── utils/scheduler.py           � Periodic watchlist runs
│
├── ⚛�  frontend/src/
│   ├── pages/
│   │   ├── Dashboard.jsx            � Landing + ticker search
│   │   ├── StockDetail.jsx          � Full prediction workspace
│   │   └── History.jsx              � Prediction history log
│   ├── components/
│   │   ├── Layout.jsx, TickerTape.jsx, LivePriceHeader.jsx
│   │   ├── StockChart.jsx           � Candlestick chart
│   │   ├── PipelineProgress.jsx     � Real-time step stepper
│   │   ├── PredictionCard.jsx, SentimentGauge.jsx
│   │   ├── TechnicalsPanel.jsx, RLStatsPanel.jsx
│   └── hooks/
│       ├── usePredictionWS.js       � WebSocket pipeline streaming
│       └── useLivePrice.js          � Live price WebSocket
│
├── 📦 models/
│   ├── LLM/Gemma-3-4B-IT/          � Local LLM (download separately)
│   └── embedding_models/            � Embedding model (download separately)
│
├── 💾 data/                         � Auto-created at runtime
└── 📜 scripts/
    ├── setup_python.sh
    ├── start_backend.sh
    ├── start_frontend.sh
    └── download_models.sh
```

---

## 🚀 Quick Start

### 1�⃣ Clone & configure

```bash
git clone <repo>
cd NewsAlphaAI
cp .env.example .env
# Edit .env — set API keys and model paths
```

### 2�⃣ Download models

```bash
pip install huggingface_hub
bash scripts/download_models.sh
```

> Or manually place models:
> - LLM → `models/LLM/Gemma-3-4B-IT/`
> - Embeddings → `models/embedding_models/`

### 3�⃣ Start backend

```bash
bash scripts/setup_python.sh      # creates .venv, installs deps
bash scripts/start_backend.sh     # http://localhost:8000
```

### 4�⃣ Start frontend

```bash
bash scripts/start_frontend.sh    # http://localhost:5173
```

### 🪟 Windows (PowerShell)

```powershell
mkdir data\news, data\stocks, data\embeddings\chroma
mkdir data\embeddings\faiss, data\memory, data\ml_models, data\rl
mkdir models\LLM

cd frontend
npm install
npm run dev
```

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `gemma` / `openai` / `mistral` / `llama` | `gemma` |
| `GEMMA_MODEL_PATH` | Path to Gemma model dir | `./models/LLM/Gemma-3-4B-IT` |
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) key | — |
| `GNEWS_API_KEY` | [gnews.io](https://gnews.io) key | — |
| `ALPHAVANTAGE_KEY` | [alphavantage.co](https://alphavantage.co) key | — |
| `VECTORDB_PROVIDER` | `chroma` or `faiss` | `chroma` |
| `LANGCHAIN_API_KEY` | LangSmith key (optional) | — |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing | `false` |
| `MEMORY_DIR` | Agent memory path | `./data/memory` |
| `OPENAI_API_KEY` | OpenAI key (if using openai provider) | — |
| `MISTRAL_MODEL_PATH` | Path to Mistral model | `./models/LLM/Mistral-7B-Instruct` |
| `LLAMA_MODEL_PATH` | Path to LLaMA model | `./models/LLM/Meta-Llama-3-8B-Instruct` |

---

## � REST API Reference

---

### 🟢 GET &nbsp;`/api/stock/{ticker}/info`

Fetch company information for a ticker symbol.

**Path Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ticker` | `string` | ✅ Yes | Stock ticker e.g. `AAPL`, `TSLA` |

**Request**
```http
GET /api/stock/AAPL/info
```

**Response** `200 OK`
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "market_cap": 2850000000000,
  "pe_ratio": 28.4,
  "52w_high": 198.23,
  "52w_low": 124.17,
  "description": "Apple Inc. designs, manufactures, and markets smartphones..."
}
```

---

### 🟢 GET &nbsp;`/api/stock/{ticker}/chart`

Fetch OHLCV candlestick data for charting.

**Path Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ticker` | `string` | ✅ Yes | Stock ticker symbol |

**Query Parameters**

| Parameter | Type | Required | Default | Options |
|---|---|---|---|---|
| `period` | `string` | � No | `30d` | `7d` / `30d` / `90d` / `1y` |

**Request**
```http
GET /api/stock/TSLA/chart?period=30d
```

**Response** `200 OK`
```json
{
  "ticker": "TSLA",
  "period": "30d",
  "candles": [
    {
      "date": "2024-01-15",
      "open": 218.3,
      "high": 225.6,
      "low": 216.1,
      "close": 223.4,
      "volume": 98234567
    }
  ]
}
```

---

### 🟢 GET &nbsp;`/api/stock/{ticker}/technicals`

Fetch computed technical indicators for a ticker.

**Path Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ticker` | `string` | ✅ Yes | Stock ticker symbol |

**Request**
```http
GET /api/stock/NVDA/technicals
```

**Response** `200 OK`
```json
{
  "ticker": "NVDA",
  "price": 875.40,
  "rsi": 62.4,
  "macd": 12.3,
  "macd_signal": 9.8,
  "macd_hist": 2.5,
  "sma_20": 860.2,
  "sma_50": 820.5,
  "ema_12": 868.9,
  "ema_26": 845.3,
  "bb_upper": 910.1,
  "bb_lower": 810.3,
  "volume_avg": 45678900,
  "atr": 18.7
}
```

---

### 🔵 POST &nbsp;`/api/predict/{ticker}`

Run the full 8-node LangGraph prediction pipeline (blocking until complete).

**Path Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ticker` | `string` | ✅ Yes | Stock ticker symbol |

**Request**
```http
POST /api/predict/AAPL
Content-Type: application/json
```

**Response** `200 OK`
```json
{
  "ticker": "AAPL",
  "direction": "UP",
  "probability": 0.7823,
  "confidence": "HIGH",
  "llm_direction": "UP",
  "llm_probability": 0.8100,
  "ml_direction": "UP",
  "ml_probability": 0.7400,
  "sentiment": "BULLISH",
  "sentiment_score": 0.65,
  "price": 189.30,
  "rsi": 58.2,
  "macd": 2.14,
  "reasoning_bullets": [
    "Strong iPhone 16 pre-order demand signals revenue beat",
    "RSI at 58 indicates healthy momentum without overbought conditions",
    "Services segment growth accelerating YoY"
  ],
  "summary": "Bullish momentum supported by strong fundamentals and positive news flow.",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Response Fields**

| Field | Type | Description |
|---|---|---|
| `direction` | `string` | Final ensemble direction: `UP` or `DOWN` |
| `probability` | `float` | Confidence probability `0.5 – 1.0` |
| `confidence` | `string` | `HIGH` (>0.72) / `MEDIUM` (>0.58) / `LOW` |
| `llm_direction` | `string` | LLM-only directional prediction |
| `llm_probability` | `float` | LLM raw probability |
| `ml_direction` | `string` | XGBoost-only directional prediction |
| `ml_probability` | `float` | XGBoost raw probability |
| `sentiment` | `string` | `BULLISH` / `BEARISH` / `NEUTRAL` |
| `sentiment_score` | `float` | Sentiment score `-1.0` to `1.0` |
| `reasoning_bullets` | `list[string]` | Key reasoning points from LLM |
| `summary` | `string` | One-sentence prediction summary |

---

### 🟢 GET &nbsp;`/api/prediction/{ticker}/history`

Retrieve stored prediction history from agent memory.

**Path Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ticker` | `string` | ✅ Yes | Stock ticker symbol |

**Request**
```http
GET /api/prediction/AAPL/history
```

**Response** `200 OK`
```json
{
  "ticker": "AAPL",
  "total": 2,
  "predictions": [
    {
      "direction": "UP",
      "probability": 0.7823,
      "confidence": "HIGH",
      "sentiment": "BULLISH",
      "timestamp": "2024-01-15T10:30:00.000Z"
    },
    {
      "direction": "DOWN",
      "probability": 0.6210,
      "confidence": "MEDIUM",
      "sentiment": "BEARISH",
      "timestamp": "2024-01-12T10:30:00.000Z"
    }
  ]
}
```

---

### 🟢 GET &nbsp;`/api/prediction/{ticker}/rl-stats`

Fetch reinforcement learning accuracy statistics for a ticker.

**Path Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ticker` | `string` | ✅ Yes | Stock ticker symbol |

**Request**
```http
GET /api/prediction/AAPL/rl-stats
```

**Response** `200 OK`
```json
{
  "ticker": "AAPL",
  "accuracy": 0.724,
  "total": 29,
  "correct": 21,
  "recent_rewards": [1.0, 1.0, -1.0, 1.0, 0.0, 1.0, 1.0, -1.0, 1.0, 1.0]
}
```

**Response Fields**

| Field | Type | Description |
|---|---|---|
| `accuracy` | `float` | Win rate `0.0 – 1.0` |
| `total` | `int` | Total resolved predictions |
| `correct` | `int` | Correct predictions |
| `recent_rewards` | `list[float]` | Last 10 rewards: `+1.0` / `-1.0` / `0.0` |

---

## 🔌 WebSocket API Reference

---

### 🟣 WS &nbsp;`ws://localhost:8000/ws/predict/{ticker}`

Streams full pipeline step updates in real-time as the prediction runs.

**Connect**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/predict/AAPL');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.step, msg.status);
};
```

**Message Format** — one message per pipeline node
```json
{
  "step": "analyse_sentiment",
  "status": "complete",
  "data": {
    "batch_sentiment": {
      "overall_sentiment": "BULLISH",
      "sentiment_score": 0.65
    },
    "logs": ["Sentiment: BULLISH (score=0.65)"]
  }
}
```

**Pipeline Steps (in order)**

| Step | Emoji | Description |
|---|---|---|
| `fetch_news` | 📰 | Fetching articles from all news sources |
| `analyse_sentiment` | 🧠 | Running LLM sentiment analysis |
| `embed_store` | 🗄� | Embedding and storing in vector DB |
| `fetch_stock` | 📊 | Fetching stock data and indicators |
| `rag_retrieve` | � | Retrieving relevant RAG context |
| `llm_reason` | 💬 | LLM generating directional reasoning |
| `ml_predict` | 🤖 | XGBoost ML prediction |
| `final_predict` | 🎯 | Ensemble combining LLM + ML |

**Final Step Message**
```json
{
  "step": "final_predict",
  "status": "complete",
  "data": {
    "final_prediction": {
      "direction": "UP",
      "probability": 0.7823,
      "confidence": "HIGH",
      "summary": "Bullish momentum supported by strong fundamentals."
    }
  }
}
```

---

### 🟣 WS &nbsp;`ws://localhost:8000/ws/live/{ticker}`

Broadcasts live price updates every 15 seconds.

**Connect**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live/TSLA');
```

**Received Message**
```json
{
  "ticker": "TSLA",
  "price": 223.45,
  "change": 2.15,
  "change_pct": 0.97,
  "volume": 12453200,
  "timestamp": "2024-01-15T14:32:00.000Z"
}
```

---

## 🔄 How the RL Loop Works

```
1. RECORD   Every prediction saved with feature vector + price
                          │
                          ▼
2. RESOLVE  After 3 days → fetch actual price → assign reward
            +1.0 (correct)  /  -1.0 (wrong)  /  0.0 (neutral)
                          │
                          ▼
3. RETRAIN  When 20+ labelled samples → retrain XGBoost
            with reward-weighted samples
                          │
                          ▼
4. IMPROVE  Correct high-confidence → upweighted (1.5x)
            Wrong predictions → downweighted (0.5x)
```

---

## 🤖 Adding a New LLM Provider

Edit `backend/models_registry/llm_registry.py`:

```python
def _load_my_model() -> BaseLanguageModel:
    # your loader here
    ...

PROVIDER_MAP["my_model"] = _load_my_model
```

Then set in `.env`:
```env
LLM_PROVIDER=my_model
```

---

## 💾 Data Directories

| Directory | Purpose | Notes |
|---|---|---|
| `data/news/{TICKER}/` | Raw fetched articles | Auto-created |
| `data/stocks/{TICKER}/` | OHLCV CSV cache | Auto-created |
| `data/embeddings/chroma/` | ChromaDB vector store | Auto-created |
| `data/memory/` | Agent long-term memory | ⚠� Back up independently |
| `data/ml_models/` | Trained XGBoost `.json` files | Created on first retrain |
| `data/rl/feedback.jsonl` | RL outcome log | JSONL, one record per line |

---

## 🔭 LangSmith Tracing

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=******
LANGCHAIN_PROJECT=NewsAlphaAI
```

View all LangGraph runs at [https://smith.langchain.com](https://smith.langchain.com)

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
