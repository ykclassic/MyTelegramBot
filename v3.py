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

# Dummy Telegram credentials (replace with real ones if needed)
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        st.error(f"Telegram Exception: {e}")

# =====================
# FETCH DATA
# =====================
@st.cache_data(ttl=300)
def fetch_ohlcv(exchange_name, symbol, timeframe, limit=300):
    # Correct ccxt exchange IDs (this was the main bug for Gate.io)
    ex_ids = {
        "XT": "xt",
        "Bitget": "bitget",
        "Gate.io": "gate"  # Correct ID is 'gate', not 'gateio'
    }
    ex_id = ex_ids.get(exchange_name)
    if not ex_id:
        st.warning(f"{exchange_name} not supported")
        return pd.DataFrame()

    try:
        exchange_class = getattr(ccxt, ex_id)
        exchange = exchange_class({
            'enableRateLimit': True,
            # 'options': {'defaultType': 'spot'},  # Uncomment if needed for spot markets
        })
        data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        st.warning(f"{exchange_name} fetch error: {e}")
        return pd.DataFrame()

# =====================
# INDICATORS (unchanged)
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
# SIGNAL ENGINE (unchanged)
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

# Sidebar inputs (fully interactive)
with st.sidebar:
    st.header("Settings")
    selected_exchange = st.selectbox("Exchange", EXCHANGES)
    selected_symbol = st.selectbox("Trading Pair", TRADING_PAIRS)
    selected_timeframe = st.selectbox("Timeframe", TIMEFRAMES)

# Auto-fetch and generate signal
st.header(f"{selected_symbol} • {selected_exchange} • {selected_timeframe}")

with st.spinner("Fetching latest OHLCV data..."):
    df = fetch_ohlcv(selected_exchange, selected_symbol, selected_timeframe, limit=300)

if df.empty or len(df) < 100:
    st.warning("Unable to fetch sufficient data. Possible causes:\n"
               "- The selected pair is not available on this exchange\n"
               "- Timeframe not supported\n"
               "- Temporary API issue\n"
               "Try a different exchange, pair, or timeframe.")
else:
    signal, score, levels = generate_signal(df)

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Signal", signal)
    col2.metric("Score", score, delta=score - 50)
    col3.metric("Entry", f"{levels['entry']:.4f}")
    col4.metric("Stop Loss", f"{levels['sl']:.4f}")
    col5.metric("TP2", f"{levels['tp2']:.4f}")

    # Direction & RR
    direction = "Long" if "BUY" in signal else "Short" if "SELL" in signal else "-"
    rr = abs((levels["tp1"] - levels["entry"]) / (levels["entry"] - levels["sl"])) if direction != "-" else None
    st.write(f"**Direction:** {direction} | **Risk:Reward (to TP1):** {rr:.2f if rr else '-'}")

    # Optional Telegram alert
    if signal != "HOLD":
        alert_message = (
            f"📢 *Trade Signal*\n\n"
            f"*Exchange:* {selected_exchange}\n"
            f"*Pair:* {selected_symbol}\n"
            f"*Timeframe:* {selected_timeframe}\n"
            f"*Signal:* {signal}\n"
            f"*Score:* {score}\n"
            f"*Entry:* {levels['entry']:.4f}\n"
            f"*SL:* {levels['sl']:.4f}\n"
            f"*TP1:* {levels['tp1']:.4f}\n"
            f"*TP2:* {levels['tp2']:.4f}"
        )
        if st.button("📲 Send Telegram Alert"):
            send_telegram(alert_message)
            st.success("Alert sent!")

    # Candlestick chart
    st.subheader("Chart with Key Levels")
    fig = go.Figure(data=[go.Candlestick(
        x=df.index[-200:],
        open=df["open"][-200:],
        high=df["high"][-200:],
        low=df["low"][-200:],
        close=df["close"][-200:]
    )])

    fig.add_hline(y=levels["entry"], line_color="blue", line_dash="dot", annotation_text="Entry")
    fig.add_hline(y=levels["sl"], line_color="red", line_dash="dot", annotation_text="SL")
    fig.add_hline(y=levels["tp1"], line_color="green", line_dash="dot", annotation_text="TP1")
    fig.add_hline(y=levels["tp2"], line_color="lime", line_dash="dot", annotation_text="TP2")

    fig.update_layout(height=600, xaxis_rangeslider_visible=False, title=f"{selected_symbol} {selected_timeframe}")
    st.plotly_chart(fig, use_container_width=True)

    last_update = df.index[-1].strftime("%Y-%m-%d %H:%M UTC")
    st.caption(f"Last candle: {last_update} • Data cached for up to 5 minutes • Demo only • Not financial advice")
