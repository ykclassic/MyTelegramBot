import sys
from pathlib import Path
# Add the project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import streamlit as st
import plotly.graph_objects as go  # Imported once at top

from config import APP_NAME, SUPPORTED_EXCHANGES, TRADING_PAIRS, TIMEFRAMES, PARAM_GRID
from data.market_data import fetch_ohlcv
from signals.generator import generate_signal
from utils.telegram import send_message

st.set_page_config(APP_NAME, layout="wide")
st.title("ProfitForge Pro v11 – MTF Confirmed Signals")

exchange = st.selectbox("Exchange", SUPPORTED_EXCHANGES)
symbols = st.multiselect("Symbols", TRADING_PAIRS, default=TRADING_PAIRS[:2])
# Timeframes selection kept but not used in loop — we force MTF logic below

for symbol in symbols:
    st.markdown("---")
    
    # === MTF DATA FETCH: 1h (entry), 4h + 1d (confirmation) ===
    df_1h = fetch_ohlcv(exchange, symbol, "1h")
    df_4h = fetch_ohlcv(exchange, symbol, "4h")
    df_1d = fetch_ohlcv(exchange, symbol, "1d")

    # Debug info
    st.write(f"Debug [{symbol}]: 1h shape = {df_1h.shape}, 4h = {df_4h.shape}, 1d = {df_1d.shape}")

    if df_1h.empty or len(df_1h) < 100 or df_4h.empty or df_1d.empty:
        st.warning(f"Insufficient data for {symbol} on required timeframes (1h/4h/1d).")
        continue

    # Generate signals on each timeframe
    signal_1h, score_1h, levels_1h = generate_signal(df_1h, PARAM_GRID[0])
    signal_4h, _, _ = generate_signal(df_4h, PARAM_GRID[0])
    signal_1d, _, _ = generate_signal(df_1d, PARAM_GRID[0])

    # Higher timeframe trend alignment
    higher_bullish = ("BUY" in signal_4h) and ("BUY" in signal_1d)
    higher_bearish = ("SELL" in signal_4h) and ("SELL" in signal_1d)

    # Final confirmed signal
    final_signal = "HOLD"
    final_score = score_1h
    final_levels = levels_1h

    if higher_bullish and "BUY" in signal_1h:
        final_signal = signal_1h
    elif higher_bearish and "SELL" in signal_1h:
        final_signal = signal_1h
    elif "BUY" in signal_1h or "SELL" in signal_1h:
        final_signal = f"WEAK {signal_1h}"  # Shows potential but unconfirmed

    # === DISPLAY RESULTS ===
    st.markdown(f"### {symbol} — Entry: 1h | Trend Confirmation: 4h + 1d")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final Signal", final_signal)
    with col2:
        st.metric("Score (1h)", final_score, delta=final_score - 50)
    with col3:
        st.write(f"**4h:** {signal_4h} | **1d:** {signal_1d}")

    # === 1H CANDlestick CHART WITH LEVELS ===
    if len(df_1h) >= 50:
        fig = go.Figure(data=[go.Candlestick(
            x=df_1h.index[-200:],
            open=df_1h["open"][-200:],
            high=df_1h["high"][-200:],
            low=df_1h["low"][-200:],
            close=df_1h["close"][-200:]
        )])

        if "BUY" in final_signal or "SELL" in final_signal:
            fig.add_hline(y=final_levels["entry"], line_color="blue", line_dash="dot", annotation_text="Entry")
            fig.add_hline(y=final_levels.get("sl", final_levels["entry"]), line_color="red", line_dash="dash", annotation_text="SL")
            fig.add_hline(y=final_levels.get("tp1", final_levels["entry"]), line_color="green", line_dash="dash", annotation_text="TP1")
            fig.add_hline(y=final_levels.get("tp2", final_levels["entry"]), line_color="lime", line_dash="dash", annotation_text="TP2")

        fig.update_layout(
            title=f"{symbol} — 1h Chart (Entry Timeframe)",
            height=600,
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough 1h data to display chart")

    # === TELEGRAM ALERT (Manual button — only on confirmed signals) ===
    if "STRONG BUY" in final_signal or "STRONG SELL" in final_signal or final_signal in ["BUY", "SELL"]:
        alert_msg = (
            f"🚨 PROFITFORGE PRO CONFIRMED SIGNAL 🚨\n\n"
            f"{symbol}\n"
            f"Signal: {final_signal}\n"
            f"Entry (1h): {final_levels['entry']:.4f}\n"
            f"Stop Loss: {final_levels['sl']:.4f}\n"
            f"TP1: {final_levels['tp1']:.4f} | TP2: {final_levels['tp2']:.4f}\n"
            f"Confirmed on 4h + 1d trend"
        )
        if st.button(f"Send Confirmed Alert: {symbol}", key=f"alert_{symbol}"):
            send_message(alert_msg)
            st.success("Alert sent to Telegram!")
    else:
        st.caption("Waiting for 4h + 1d confirmation — no strong aligned signal yet.")
