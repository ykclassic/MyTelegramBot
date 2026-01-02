# =========================================================
# PROFITFORGE – SINGLE FILE VERSION (STABLE DEMO BUILD)
# =========================================================

import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="ProfitForge – Demo", layout="wide")

# --- Dummy Telegram Credentials (for demo only) ---
TELEGRAM_BOT_TOKEN = "123456789:DEMO_TELEGRAM_TOKEN"
TELEGRAM_CHAT_ID = "123456789"

# =========================================================
# TELEGRAM
# =========================================================

def send_telegram(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        st.warning(f"Telegram error: {e}")

# =========================================================
# MARKET DATA
# =========================================================

def fetch_ohlcv(symbol, timeframe, limit=200):
    exchange = ccxt.binance()
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# =========================================================
# INDICATORS
# =========================================================

def rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def macd(df):
    exp1 = df["close"].ewm(span=12, adjust=False).mean()
    exp2 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    df["ATR"] = ranges.max(axis=1).rolling(period).mean()
    return df

def ichimoku(df):
    high9 = df["high"].rolling(9).max()
    low9 = df["low"].rolling(9).min()
    df["Tenkan"] = (high9 + low9) / 2

    high26 = df["high"].rolling(26).max()
    low26 = df["low"].rolling(26).min()
    df["Kijun"] = (high26 + low26) / 2

    df["SpanA"] = ((df["Tenkan"] + df["Kijun"]) / 2).shift(26)
    df["SpanB"] = ((df["high"].rolling(52).max() +
                     df["low"].rolling(52).min()) / 2).shift(26)
    return df

# =========================================================
# SIGNAL ENGINE (FIXED)
# =========================================================

def generate_signal(df):
    df = rsi(df)
    df = macd(df)
    df = atr(df)
    df = ichimoku(df)

    last = df.iloc[-1]
    score = 50

    if last["RSI"] < 30:
        score += 20
    if last["RSI"] > 70:
        score -= 20
    if last["MACD"] > last["MACD_Signal"]:
        score += 15
    if last["MACD"] < last["MACD_Signal"]:
        score -= 15

    cloud_top = max(last["SpanA"], last["SpanB"])
    cloud_bottom = min(last["SpanA"], last["SpanB"])

    if last["close"] > cloud_top:
        score += 15
    if last["close"] < cloud_bottom:
        score -= 15

    # SIGNAL TYPE
    if score >= 80:
        signal = "STRONG BUY"
    elif score >= 65:
        signal = "BUY"
    elif score <= 20:
        signal = "STRONG SELL"
    elif score <= 35:
        signal = "SELL"
    else:
        signal = "HOLD"

    entry = last["close"]
    atr_val = last["ATR"]

    levels = {
        "entry": entry,
        "sl": entry - atr_val * 2 if "BUY" in signal else entry + atr_val * 2,
        "tp1": entry * 1.03 if "BUY" in signal else entry * 0.97,
        "tp2": entry * 1.06 if "BUY" in signal else entry * 0.94
    }

    return signal, score, levels

# =========================================================
# UI
# =========================================================

st.title("🔥 ProfitForge — Signal Engine (Demo)")

symbol = st.selectbox("Trading Pair", ["BTC/USDT", "ETH/USDT"])
timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h", "4h"])

if st.button("Generate Signal"):

    df = fetch_ohlcv(symbol, timeframe)
    signal, score, levels = generate_signal(df)

    st.subheader("📊 Signal Summary")

    st.write({
        "Signal": signal,
        "Score": score,
        "Entry": round(levels["entry"], 4),
        "Stop Loss": round(levels["sl"], 4),
        "Take Profit 1": round(levels["tp1"], 4),
        "Take Profit 2": round(levels["tp2"], 4),
    })

    # Send Telegram Alert (only actionable)
    if signal != "HOLD":
        send_telegram(
            f"""
📊 *Trade Signal*

Pair: {symbol}
TF: {timeframe}

Signal: {signal}
Entry: {levels['entry']:.4f}
SL: {levels['sl']:.4f}
TP1: {levels['tp1']:.4f}
TP2: {levels['tp2']:.4f}
"""
        )

    st.success("Signal processed successfully.")

# =========================================================
# FOOTER
# =========================================================

st.caption("ProfitForge • Demo Build • Not Financial Advice")
