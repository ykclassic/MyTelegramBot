import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import streamlit as st
import plotly.graph_objects as go

from config import APP_NAME, SUPPORTED_EXCHANGES, TRADING_PAIRS, PARAM_GRID
from data.market_data import fetch_ohlcv
from signals.generator import generate_signal
from utils.telegram import send_message

# === AESTHETICS & THEME ===
st.set_page_config(APP_NAME, layout="wide", page_icon="🔥")
st.markdown("""
<style>
    .big-font { font-size:50px !important; font-weight:bold; text-align:center; }
    .signal-buy { color:#00ff00; }
    .signal-sell { color:#ff0000; }
    .signal-hold { color:#ffff00; }
    .card { padding: 20px; border-radius: 10px; box-shadow: 5px 5px 15px #aaaaaa; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">🔥 ProfitForge Pro v12 🔥</p>', unsafe_allow_html=True)
st.caption("Multi-Timeframe Confirmed Signals | Entry: 1h | Trend: 4h + 1d")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    exchange = st.selectbox("Exchange", SUPPORTED_EXCHANGES)
    symbols = st.multiselect("Symbols (Volatile Selection)", TRADING_PAIRS, default=["DOGE/USDT", "SHIB/USDT", "PEPE/USDT"])

for symbol in symbols:
    with st.container():
        st.markdown(f"<div class='card'><h3>📊 {symbol}</h3></div>", unsafe_allow_html=True)

        # MTF Fetch
        df_1h = fetch_ohlcv(exchange, symbol, "1h")
        df_4h = fetch_ohlcv(exchange, symbol, "4h")
        df_1d = fetch_ohlcv(exchange, symbol, "1d")

        if df_1h.empty or len(df_1h) < 100:
            st.warning("Insufficient data — skipping.")
            continue

        signal_1h, score_1h, levels_1h = generate_signal(df_1h, PARAM_GRID[0])
        signal_4h, _, _ = generate_signal(df_4h, PARAM_GRID[0])
        signal_1d, _, _ = generate_signal(df_1d, PARAM_GRID[0])

        higher_bullish = ("BUY" in signal_4h) and ("BUY" in signal_1d)
        higher_bearish = ("SELL" in signal_4h) and ("SELL" in signal_1d)

        final_signal = "HOLD"
        if higher_bullish and "BUY" in signal_1h: final_signal = signal_1h
        elif higher_bearish and "SELL" in signal_1h: final_signal = signal_1h

        # Signal Badge
        color_class = "signal-hold"
        if "BUY" in final_signal: color_class = "signal-buy"
        if "SELL" in final_signal: color_class = "signal-sell"

        st.markdown(f"<h2 class='{color_class}'>Signal: {final_signal}</h2>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Score (1h)", f"{score_1h}/100")
        with col2: st.metric("4h Trend", signal_4h)
        with col3: st.metric("1d Trend", signal_1d)

        # Chart in expander for clean look
        with st.expander("📈 View 1h Chart & Levels", expanded=True):
            fig = go.Figure(data=[go.Candlestick(x=df_1h.index[-200:], open=df_1h["open"][-200:], high=df_1h["high"][-200:], low=df_1h["low"][-200:], close=df_1h["close"][-200:])])
            if "BUY" in final_signal or "SELL" in final_signal:
                fig.add_hline(y=levels_1h["entry"], line_color="cyan", line_dash="dot", annotation_text="Entry 🚀")
                fig.add_hline(y=levels_1h["sl"], line_color="red", annotation_text="Stop Loss 🛑")
                fig.add_hline(y=levels_1h["tp2"], line_color="lime", annotation_text="Take Profit 💰")
            fig.update_layout(height=600, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # Alert Button
        if "STRONG" in final_signal or final_signal in ["BUY", "SELL"]:
            if st.button(f"🚨 Send Alert: {symbol}", type="primary"):
                send_message(f"🔥 {final_signal} on {symbol}!\nEntry: {levels_1h['entry']:.4f}\nConfirmed on higher TFs")
                st.balloons()

st.success("Scan complete — monitoring volatile pairs for aligned signals!")
