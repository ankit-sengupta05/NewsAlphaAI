"""
backend/tools/stock_tools.py
LangGraph tools for stock data fetching & feature engineering.
"""
from __future__ import annotations


from datetime import datetime

import pandas as pd
from langchain_core.tools import tool
from loguru import logger

from backend.core.config import settings


def _save_stock_data(df: pd.DataFrame, ticker: str):
    dest = settings.stock_data_dir / ticker
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    df.to_csv(dest / f"ohlcv_{stamp}.csv")


@tool
def fetch_stock_ohlcv(ticker: str, period: str = "30d") -> dict:
    """
    Fetch OHLCV data for a ticker using yfinance.
    Returns a dict with columns and data suitable for feature engineering.
    period: '7d', '30d', '90d', '1y'
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return {"error": f"No data for {ticker}"}

        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = df.index.strftime("%Y-%m-%d")
        _save_stock_data(df, ticker)

        return {
            "ticker": ticker,
            "period": period,
            "columns": list(df.columns),
            "data": df.to_dict(orient="index"),
        }
    except Exception as e:
        logger.error(f"yfinance error for {ticker}: {e}")
        return {"error": str(e)}


@tool
def compute_technical_features(ticker: str) -> dict:
    """
    Compute technical indicators (RSI, MACD, BB, SMA, EMA, volume ratio)
    from the latest cached OHLCV data.
    Returns a flat feature dict suitable for the ML model.
    """
    try:
        import yfinance as yf
        df = yf.Ticker(ticker).history(period="60d")
        if df.empty:
            return {"error": "no data"}

        close = df["Close"]
        volume = df["Volume"]

        # ── SMA / EMA ─────────────────────────────────────────────────────────
        sma_5 = close.rolling(5).mean().iloc[-1]
        sma_20 = close.rolling(20).mean().iloc[-1]
        ema_12 = close.ewm(span=12).mean().iloc[-1]
        ema_26 = close.ewm(span=26).mean().iloc[-1]

        # ── MACD ──────────────────────────────────────────────────────────────
        macd = ema_12 - ema_26
        signal = (close.ewm(span=12).mean() - close.ewm(span=26).mean()).ewm(span=9).mean().iloc[-1]
        macd_hist = macd - signal

        # ── RSI ───────────────────────────────────────────────────────────────
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        rsi = (100 - 100 / (1 + rs)).iloc[-1]

        # ── Bollinger Bands ───────────────────────────────────────────────────
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = (bb_mid + 2 * bb_std).iloc[-1]
        bb_lower = (bb_mid - 2 * bb_std).iloc[-1]
        bb_pct = (close.iloc[-1] - bb_lower) / (bb_upper - bb_lower + 1e-9)

        # ── Volume ────────────────────────────────────────────────────────────
        vol_ratio = volume.iloc[-1] / (volume.rolling(20).mean().iloc[-1] + 1e-9)

        # ── Price change features ─────────────────────────────────────────────
        price_now = close.iloc[-1]
        price_1d = close.iloc[-2] if len(close) > 1 else price_now
        price_5d = close.iloc[-6] if len(close) > 5 else price_now

        return {
            "ticker": ticker,
            "price": round(float(price_now), 4),
            "change_1d_pct": round(float((price_now - price_1d) / (price_1d + 1e-9) * 100), 4),
            "change_5d_pct": round(float((price_now - price_5d) / (price_5d + 1e-9) * 100), 4),
            "sma_5": round(float(sma_5), 4),
            "sma_20": round(float(sma_20), 4),
            "ema_12": round(float(ema_12), 4),
            "ema_26": round(float(ema_26), 4),
            "macd": round(float(macd), 4),
            "macd_signal": round(float(signal), 4),
            "macd_hist": round(float(macd_hist), 4),
            "rsi": round(float(rsi), 2),
            "bb_pct": round(float(bb_pct), 4),
            "vol_ratio": round(float(vol_ratio), 4),
            "sma_crossover": int(sma_5 > sma_20),
        }
    except Exception as e:
        logger.error(f"Feature engineering error for {ticker}: {e}")
        return {"error": str(e)}


@tool
def get_stock_info(ticker: str) -> dict:
    """Return basic info (company name, sector, market cap) for a ticker."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        return {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", ""),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}
