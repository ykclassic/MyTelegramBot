import sys 
import plotly.graph_objects as go
from pathlib import Path 
# Add the project root directory to Python path 
sys.path.insert(0, str(Path(__file__).parent.resolve()))
import streamlit as st
from config import APP_NAME, SUPPORTED_EXCHANGES, TRADING_PAIRS, TIMEFRAMES, PARAM_GRID
from data.market_data import fetch_ohlcv
from signals.generator import generate_signal
from backtest.engine import backtest
from utils.telegram import send_message
from datetime import datetime, timezone

st.set_page_config(APP_NAME, layout="wide")
st.title(APP_NAME)

exchange = st.selectbox("Exchange", SUPPORTED_EXCHANGES)
symbols = st.multiselect("Symbols", TRADING_PAIRS, default=TRADING_PAIRS[:2])
timeframes = st.multiselect("Timeframes", TIMEFRAMES, default=["1h"])

for symbol in symbols:
    for tf in timeframes:
        df = fetch_ohlcv(exchange, symbol, tf)
                # === FIX 1: Debug data fetch ===
        st.write(f"Debug [{symbol} {tf}]: DataFrame shape = {df.shape}")
        if df.empty:
            st.error(f"No data fetched for {symbol} on {exchange} ({tf}). Check symbol/timeframe compatibility.")
        else:
            st.write("Debug: First few rows", df.head())
        # ================================
        if df.empty:
            continue

        signal, score, levels = generate_signal(df, PARAM_GRID[0])

        st.markdown(f"### {symbol} ({tf})")
        st.write(f"Signal: **{signal}** | Score: `{score}`")
                # === FIX 4: Safe candlestick chart ===
        if len(df) >= 50:  # Only show chart if enough data
            import plotly.graph_objects as go

            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close']
            )])

            # Add entry, SL, TP lines if signal is active
            if "BUY" in signal or "SELL" in signal:
                fig.add_hline(y=levels['entry'], line_dash="dot", line_color="blue", annotation_text="Entry")
                fig.add_hline(y=levels.get('sl', levels['entry']), line_dash="dash", line_color="red", annotation_text="Stop Loss")
                fig.add_hline(y=levels.get('tp1', levels['entry']), line_dash="dash", line_color="green", annotation_text="TP1")

            fig.update_layout(title=f"{symbol} {tf} - {exchange}", height=600)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to display chart")
        # =====================================

        if "BUY" in signal or "SELL" in signal:
            send_message(
                f"{symbol} {tf}\nSignal: {signal}\nEntry: {levels['entry']:.2f}"
            )
