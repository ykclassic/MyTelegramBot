import ccxt
import pandas as pd
from datetime import timezone

def fetch_ohlcv(exchange_id, symbol, timeframe="1h", limit=500):
    exchange = getattr(ccxt, exchange_id)()
    exchange.enableRateLimit = True

    if not exchange.has.get("fetchOHLCV", False):
        return pd.DataFrame()

    try:
        data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if not data:
        st.warning(f"No data returned for {symbol} {timeframe} on {exchange_name}")
        return pd.DataFrame()
        df = pd.DataFrame(data, columns=["timestamp","Open","High","Low","Close","Volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)
        return df
    except Exception:
        return pd.DataFrame()
