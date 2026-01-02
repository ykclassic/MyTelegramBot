import streamlit as st
import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import plotly.graph_objects as go

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="ProfitForge Demo", layout="wide")

# Dummy Telegram credentials
TELEGRAM_BOT_TOKEN = "8367963721:AAH6B819_DevFNpZracbJ5EmHrDR3DKZeR4"
TELEGRAM_CHAT_ID = "865482105"

TRADING_PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
TIMEFRAMES = ["5m", "15m", "1h", "4h"]
EXCHANGES = ["XT", "Bitget", "Gate.io"]

# =====================
# SESSION
# =====================
def get_trading_session():
    utc_now = datetime.now(timezone.utc) + timedelta(hours=1)
    hour = utc_now.hour
    if 0 <= hour < 8: return "Asian Session", "#3498db"
    elif 8 <= hour < 12: return "London Open", "#2ecc71"
    elif 12 <= hour < 16: return "NY + London Overlap", "#e67e22"
    elif 16 <= hour < 21: return "New York", "#e74c3c"
    else: return "Quiet Hours", "#95a5a6"

# =====================
# TELEGRAM ALERT
# =====================
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        st.write("📡 Telegram Status:", response.status_code)
    except Exception as e:
        st.error(f"Telegram Exception: {e}")

# =====================
# FETCH DATA
# =====================
@st.cache_data(ttl=300)
def fetch_ohlcv(exchange_name, symbol, timeframe, limit=200):
    exchanges = {
        "XT": ccxt.xt(),
        "Bitget": ccxt.bitget(),
        "Gate.io": ccxt.gateio()
    }
    exchange = exchanges.get(exchange_name)
    if not exchange:
        st.warning(f"{exchange_name} not supported")
        return pd.DataFrame()
    try:
        exchange.enableRateLimit = True
        data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        st.warning(f"{exchange_name} fetch error: {e}")
        return pd.DataFrame()

# =====================
# INDICATORS
# =====================
def rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta>0,0).rolling(period).mean()
    loss = -delta.where(delta<0,0).rolling(period).mean()
    df["RSI"] = 100 - 100/(1 + gain/loss)
    return df

def macd(df):
    exp1 = df["close"].ewm(span=12, adjust=False).mean()
    exp2 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(period).mean()
    return df

def ichimoku(df):
    df["Tenkan"] = (df["high"].rolling(9).max() + df["low"].rolling(9).min()) / 2
    df["Kijun"] = (df["high"].rolling(26).max() + df["low"].rolling(26).min()) / 2
    df["SpanA"] = ((df["Tenkan"] + df["Kijun"]) / 2).shift(26)
    df["SpanB"] = ((df["high"].rolling(52).max() + df["low"].rolling(52).min()) / 2).shift(26)
    return df

# =====================
# SIGNAL ENGINE
# =====================
def generate_signal(df):
    df = rsi(df)
    df = macd(df)
    df = atr(df)
    df = ichimoku(df)
    last = df.iloc[-1]
    score = 50
    if last["RSI"]<30: score+=20
    if last["RSI"]>70: score-=20
    if last["MACD"]>last["MACD_Signal"]: score+=15
    if last["MACD"]<last["MACD_Signal"]: score-=15
    cloud_top = max(last["SpanA"], last["SpanB"])
    cloud_bottom = min(last["SpanA"], last["SpanB"])
    if last["close"]>cloud_top: score+=15
    if last["close"]<cloud_bottom: score-=15
    if score>=80: signal="STRONG BUY"
    elif score>=65: signal="BUY"
    elif score<=20: signal="STRONG SELL"
    elif score<=35: signal="SELL"
    else: signal="HOLD"
    entry = last["close"]
    atr_val = last["ATR"]
    levels = {
        "entry": entry,
        "sl": entry-atr_val*2 if "BUY" in signal else entry+atr_val*2,
        "tp1": entry*1.03 if "BUY" in signal else entry*0.97,
        "tp2": entry*1.06 if "BUY" in signal else entry*0.94
    }
    return signal, score, levels

# =====================
# DASHBOARD
# =====================
st.title("🔥 ProfitForge — Signal Engine (Demo)")

# Session badge
session_name, session_color = get_trading_session()
st.markdown(
    f'<div style="padding:10px; color:white; background-color:{session_color}; '
    f'border-radius:5px; width:fit-content;">'
    f'🕒 Current Session: {session_name} (UTC+1)</div>', 
    unsafe_allow_html=True
)

# Sidebar selections
with st.sidebar:
    exchange_name = st.selectbox("Exchange", EXCHANGES)
    symbol = st.selectbox("Trading Pair", TRADING_PAIRS)
    timeframe = st.selectbox("Timeframe", TIMEFRAMES)
    generate_signal_btn = st.button("Generate Signal")

# Generate signal
if generate_signal_btn:
    df = fetch_ohlcv(exchange_name, symbol, timeframe)
    if df.empty:
        st.warning("No data available.")
    else:
        signal, score, levels = generate_signal(df)
        st.subheader("📊 Signal Summary")
        st.write({
            "Exchange": exchange_name,
            "Signal": signal,
            "Score": score,
            "Entry": round(levels["entry"],4),
            "Stop Loss": round(levels["sl"],4),
            "Take Profit 1": round(levels["tp1"],4),
            "Take Profit 2": round(levels["tp2"],4)
        })
        if signal != "HOLD":
            send_telegram(
                f"📢 Trade Signal\n\nExchange: {exchange_name}\nPair: {symbol}\nTF: {timeframe}\nSignal: {signal}\nEntry: {levels['entry']:.4f}\nSL: {levels['sl']:.4f}\nTP1: {levels['tp1']:.4f}\nTP2: {levels['tp2']:.4f}"
            )
        # Candlestick
        fig = go.Figure(data=[go.Candlestick(
            x=df.index[-100:], open=df["open"][-100:], high=df["high"][-100:],
            low=df["low"][-100:], close=df["close"][-100:]
        )])
        fig.add_hline(y=levels["entry"], line_color="blue", line_dash="dot", annotation_text="Entry")
        fig.add_hline(y=levels["sl"], line_color="red", line_dash="dot", annotation_text="SL")
        fig.add_hline(y=levels["tp1"], line_color="green", line_dash="dot", annotation_text="TP1")
        fig.add_hline(y=levels["tp2"], line_color="green", line_dash="dot", annotation_text="TP2")
        fig.update_layout(height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

st.caption("ProfitForge • Demo Build • Not Financial Advice")
