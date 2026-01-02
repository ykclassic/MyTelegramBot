import sys 
from pathlib import Path 
# Add the project root directory to Python path 
sys.path.insert(0, str(Path(__file__).parent))
import streamlit as st
from config import *
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
        if df.empty:
            continue

        signal, score, levels = generate_signal(df, PARAM_GRID[0])

        st.markdown(f"### {symbol} ({tf})")
        st.write(f"Signal: **{signal}** | Score: `{score}`")

        if "BUY" in signal or "SELL" in signal:
            send_message(
                f"{symbol} {tf}\nSignal: {signal}\nEntry: {levels['entry']:.2f}"
            )
