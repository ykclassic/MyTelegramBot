# ================================
# PROFITFORGE — SINGLE FILE VERSION
# ================================

import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import plotly.graph_objects as go

# ================================
# CONFIG
# ================================

APP_NAME = "ProfitForge Pro (Single File Demo)"

# ⚠️ DUMMY / PLACEHOLDER CREDENTIALS (FOR DEMO PURPOSES ONLY)
TELEGRAM_TOKEN = "123456789:DEMO_FAKE_TELEGRAM_TOKEN"
TELEGRAM_CHAT_ID = "000000000"

TRADING_PAIRS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT",
    "BNB/USDT", "XRP/USDT"
]

TIMEFRAMES = ["15m", "1h", "4h"]

# ================================
# TELEGRAM
# ================================

def send_telegram(message):
    """
    Dummy-safe Telegram sender.
    Will fail silently if token is invalid.
    """
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=5
        )
    except:
        pass


# ================================
# MARKET DATA
# ================================

@st.cache_data(ttl=300)
def fetch_ohlcv(exchange_id, symbol, timeframe, limit=300):
    exchange = getattr(ccxt, exchange_id)()
    exchange.enableRateLimit = True

    try:
        data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(
            data,
            columns=["time", "Open", "High", "Low", "Close", "Volume"]
        )
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        df.set_index("time", inplace=True)
        return df
    except:
        return pd.DataFrame()


# ================================
# INDICATORS
# ================================

def rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def macd(df, fast=12, slow=26, signal=9):
    fast_ema = df["Close"].ewm(span=fast, adjust=False).mean()
    slow_ema = df["Close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = fast_ema - slow_ema
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    return df


def atr(df, period=14):
    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(period).mean()
    return df


def ichimoku(df):
    df["Conv"] = (df["High"].rolling(9).max() + df["Low"].rolling(9).min()) / 2
    df["Base"] = (df["High"].rolling(26).max() + df["Low"].rolling(26).min()) / 2
    df["SpanA"] = ((df["Conv"] + df["Base"]) / 2).shift(26)
    df["SpanB"] = ((df["High"].rolling(52).max() + df["Low"].rolling(52).min()) / 2).shift(26)
    return df


# ================================
# SIGNAL ENGINE
# ================================

def generate_signal(df):
    df = atr(df)
    df = rsi(df)
    df = macd(df)
    df = ichimoku(df)

    last = df.iloc[-1]
    score = 50

    if last["RSI"] < 30: score += 20
    if last["RSI"] > 70: score -= 20
    if last["MACD"] > last["MACD_Signal"]: score += 15
    if last["MACD"] < last["MACD_Signal"]: score -= 15

    cloud_top = max(last["SpanA"], last["SpanB"])
    cloud_bottom = min(last["SpanA"], last["SpanB"])

    if last["Close"] > cloud_top: score += 15
    if last["Close"] < cloud_bottom: score -= 15

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

    atr_val = last["ATR"]
    entry = last["Close"]

    return signal, score, {
        "entry": entry,
        "sl": entry - atr_val * 2 if "BUY" in signal else entry + atr_val * 2,
        "tp1": entry * 1.03 if "BUY" in signal else entry * 0.97,
        "tp2": entry * 1.06 if "BUY" in signal else entry * 0.94
    }


# ================================
# STREAMLIT UI
# ================================

st.set_page_config(APP_NAME, layout="wide")
st.title(APP_NAME)

exchange = st.selectbox("Exchange", ["binance", "bitget", "gateio"])
symbols = st.multiselect("Symbols", TRADING_PAIRS, default=["BTC/USDT"])
timeframes = st.multiselect("Timeframes", TIMEFRAMES, default=["1h"])

for symbol in symbols:
    for tf in timeframes:
        df = fetch_ohlcv(exchange, symbol, tf)
        if df.empty:
            st.warning(f"No data for {symbol} ({tf})")
            continue

        signal, score, levels = generate_signal(df)

        st.subheader(f"{symbol} — {tf}")
        st.write(f"Signal: **{signal}** | Score: `{score}`")

        if "BUY" in signal or "SELL" in signal:
            send_telegram(
                f"{symbol} {tf}\nSignal: {signal}\nEntry: {levels['entry']:.2f}"
            )

        fig = go.Figure()
        fig.add_candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"]
        )

        fig.add_hline(y=levels["entry"], line_dash="dot", line_color="blue")
        fig.add_hline(y=levels["sl"], line_dash="dot", line_color="red")
        fig.add_hline(y=levels["tp1"], line_dash="dot", line_color="green")

        fig.update_layout(height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
