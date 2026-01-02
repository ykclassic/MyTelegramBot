import ccxt
import pandas as pd
import streamlit as st  # <-- Added: required for st.warning
from datetime import timezone


def fetch_ohlcv(exchange_id, symbol, timeframe="1h", limit=500):
    """
    Fetch OHLCV data from the specified exchange using ccxt.
    
    Args:
        exchange_id (str): ccxt exchange ID (e.g., 'xt', 'gate', 'binance')
        symbol (str): Trading pair (e.g., 'BTC/USDT')
        timeframe (str): Candle timeframe (default '1h')
        limit (int): Number of candles to fetch (default 500)
    
    Returns:
        pd.DataFrame: DataFrame with OHLCV data, indexed by timestamp
    """
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'enableRateLimit': True,  # Respect exchange rate limits
        })

        # Check if the exchange supports fetchOHLCV
        if not exchange.has.get('fetchOHLCV', False):
            st.warning(f"{exchange_id.upper()} does not support fetching OHLCV data.")
            return pd.DataFrame()

        # Fetch the data
        data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

        # === FIX 3: Handle empty data ===
        if not data:
            st.warning(f"No data returned for {symbol} ({timeframe}) on {exchange_id.upper()}.")
            return pd.DataFrame()
        # ===============================

        # Create DataFrame
        df = pd.DataFrame(
            data,
            columns=["timestamp", "Open", "High", "Low", "Close", "Volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)

        return df

    except Exception as e:
        # Optional: more detailed warning (uncomment if needed)
        # st.error(f"Error fetching data for {symbol} on {exchange_id}: {str(e)}")
        st.warning(f"Failed to fetch data for {symbol} ({timeframe}) on {exchange_id.upper()}.")
        return pd.DataFrame()
