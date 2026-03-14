# NewsAlphaAI 🧠📈

> AI-powered stock direction prediction using real-time news, LLM reasoning,
> RAG pipelines, LangGraph orchestration, and reinforcement learning feedback.

---

## Architecture

```
News APIs (NewsAPI / GNews / AlphaVantage)
          │
          ▼
  LangGraph Pipeline (8 nodes)
  ┌────────────────────────────────────────────────────�
  │  fetch_news → analyse_sentiment → embed_store       │
  │      → fetch_stock → rag_retrieve → llm_reason      │
  │          → ml_predict → final_predict (ensemble)    │
  └────────────────────────────────────────────────────┘
          │
          ▼
  FastAPI Backend  �──WebSocket──→  React Frontend
  (REST + WS)                       (Upstox-style UI)
          │
          ▼
   RL Feedback Loop  ──retrains──→  XGBoost ML Model
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemma-3-4B-IT (local) via HuggingFace Transformers |
| Orchestration | LangGraph + LangChain |
| Observability | LangSmith |
| Vector DB | ChromaDB (default) / FAISS |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| ML Model | XGBoost + scikit-learn |
| RL Feedback | Custom policy-gradient-inspired loop |
| Backend | FastAPI + WebSockets + APScheduler |
| Frontend | React + Vite + TailwindCSS + lightweight-charts |

---

## Project Structure

```
NewsAlphaAI/
├── .env.example                   � All secrets & paths
├── backend/
│   ├── api/
│   │   ├── main.py                � FastAPI app + WebSocket endpoints
│   │   └── lifespan.py            � APScheduler background jobs
│   ├── core/
│   │   └── config.py              � Central pydantic-settings config
│   ├── models_registry/
│   │   ├── llm_registry.py        � Modular LLM loader (Gemma/OpenAI/Mistral/LLaMA)
│   │   └── vectordb_registry.py   � Chroma/FAISS factory
│   ├── memory/
│   │   └── memory_manager.py      � Agent long-term memory (separate dir)
│   ├── tools/                     � LangGraph @tool functions
│   │   ├── news_tools.py          � NewsAPI / GNews / AlphaVantage fetchers
│   │   ├── stock_tools.py         � yfinance + technical indicators
│   │   ├── embedding_tools.py     � Embed + store / RAG retrieve
│   │   └── sentiment_tools.py     � LLM sentiment analysis
│   ├── pipelines/
│   │   └── prediction_pipeline.py � Full LangGraph pipeline (8 nodes)
│   ├── ml/
│   │   └── prediction_model.py    � XGBoost binary classifier
│   ├── rl/
│   │   └── feedback_loop.py       � RL outcome tracking + auto-retrain
│   └── utils/
│       └── scheduler.py           � Periodic watchlist runs
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      � Landing + ticker search
│   │   │   ├── StockDetail.jsx    � Full prediction workspace
│   │   │   └── History.jsx        � Prediction history log
│   │   ├── components/
│   │   │   ├── Layout.jsx         � Sidebar + ticker tape
│   │   │   ├── TickerTape.jsx     � Live scrolling price bar
│   │   │   ├── LivePriceHeader.jsx
│   │   │   ├── StockChart.jsx     � Candlestick via lightweight-charts
│   │   │   ├── PipelineProgress.jsx � Real-time step stepper
│   │   │   ├── PredictionCard.jsx � Main prediction result
│   │   │   ├── SentimentGauge.jsx
│   │   │   ├── TechnicalsPanel.jsx
│   │   │   └── RLStatsPanel.jsx
│   │   ├── hooks/
│   │   │   ├── usePredictionWS.js � WebSocket pipeline streaming
│   │   │   └── useLivePrice.js    � Live price WebSocket
│   │   └── utils/api.js
│   └── package.json
│
├── data/                          � Auto-created at runtime
│   ├── news/{TICKER}/             � Raw news JSON
│   ├── stocks/{TICKER}/           � OHLCV CSV cache
│   ├── embeddings/chroma/         � Vector DB
│   ├── memory/{TICKER}_memory.json � Agent memory (SEPARATE from news/stocks)
│   ├── ml_models/                 � Trained XGBoost models
│   └── rl/feedback.jsonl          � RL outcome log
│
├── models/LLM/Gemma-3-4B-IT/     � Place your local model here
└── scripts/
    ├── setup_python.sh
    ├── start_backend.sh
    └── start_frontend.sh
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo>
cd NewsAlphaAI
cp .env.example .env
# Edit .env — at minimum set your API keys and GEMMA_MODEL_PATH
```

### 2. Place your Gemma model

```bash
# Copy or symlink your Gemma-3-4B-IT model directory:
mkdir -p models/LLM
cp -r /path/to/Gemma-3-4B-IT models/LLM/
```

### 3. Backend

```bash
bash scripts/setup_python.sh      # creates .venv, installs deps
bash scripts/start_backend.sh     # starts on http://localhost:8000
```

### 4. Frontend

```bash
bash scripts/start_frontend.sh    # installs npm deps + starts on http://localhost:5173
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `gemma` / `openai` / `mistral` / `llama` | `gemma` |
| `GEMMA_MODEL_PATH` | Absolute or relative path to model dir | `./models/LLM/Gemma-3-4B-IT` |
| `NEWSAPI_KEY` | newsapi.org free key | — |
| `GNEWS_API_KEY` | gnews.io free key | — |
| `ALPHAVANTAGE_KEY` | alphavantage.co free key | — |
| `VECTORDB_PROVIDER` | `chroma` or `faiss` | `chroma` |
| `LANGCHAIN_API_KEY` | LangSmith key (optional) | — |
| `MEMORY_DIR` | Agent memory location (separate!) | `./data/memory` |

---

## Adding a New LLM Provider

Edit `backend/models_registry/llm_registry.py`:

```python
def _load_my_model() -> BaseLanguageModel:
    # your loader here
    ...

PROVIDER_MAP["my_model"] = _load_my_model
```

Then set `LLM_PROVIDER=my_model` in `.env`.

---

## WebSocket Endpoints

| Endpoint | Description |
|---|---|
| `ws://localhost:8000/ws/predict/{ticker}` | Streams full pipeline steps in real-time |
| `ws://localhost:8000/ws/live/{ticker}` | Broadcasts live price updates every 15s |

---

## REST Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/stock/{ticker}/info` | Company info |
| GET | `/api/stock/{ticker}/chart?period=30d` | OHLCV data |
| GET | `/api/stock/{ticker}/technicals` | Technical indicators |
| POST | `/api/predict/{ticker}` | Run prediction (blocking) |
| GET | `/api/prediction/{ticker}/history` | Prediction memory |
| GET | `/api/prediction/{ticker}/rl-stats` | RL accuracy stats |

---

## Data Directories

| Purpose | Path |
|---|---|
| Raw news articles | `data/news/{TICKER}/` |
| OHLCV cache | `data/stocks/{TICKER}/` |
| Vector embeddings | `data/embeddings/chroma/` |
| **Agent memory** | `data/memory/` � **intentionally separate** |
| ML models | `data/ml_models/` |
| RL feedback log | `data/rl/feedback.jsonl` |

> Agent memory is stored in its own isolated directory so it can be backed up,
> inspected, or reset independently of the raw data caches.

---

## How the RL Loop Works

1. Every prediction is saved to `data/rl/feedback.jsonl` with its feature vector and price at prediction time.
2. After 3 days, the actual price move is fetched and a reward is assigned: `+1` (correct), `-1` (wrong), `0` (neutral).
3. When 20+ labelled samples accumulate for a ticker, XGBoost is retrained with reward-weighted samples.
4. High-confidence correct predictions get extra weight; wrong ones are downweighted.

---

## LangSmith Tracing

Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY=******` in `.env`.
All LangGraph runs will appear in your LangSmith dashboard at https://smith.langchain.com

cd C:\Projects\NewsAlphaAI\frontend
npm install

cd C:\Projects\NewsAlphaAI\frontend
npm run dev

cd C:\Projects\NewsAlphaAI
mkdir data\news
mkdir data\stocks
mkdir data\embeddings\chroma
mkdir data\embeddings\faiss
mkdir data\memory
mkdir data\ml_models
mkdir data\rl
mkdir models\LLM
