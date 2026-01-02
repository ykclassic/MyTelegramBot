import os

# ===== GENERAL =====
APP_NAME = "ProfitForge Pro v10"

# ===== TELEGRAM =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== EXCHANGES =====
SUPPORTED_EXCHANGES = ["binance", "bitget", "gateio", "xt"]

# ===== TRADING =====
TRADING_PAIRS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
    "XRP/USDT", "ADA/USDT", "LTC/USDT"
]

TIMEFRAMES = ["5m", "15m", "1h", "4h"]

# ===== BACKTEST PARAM GRID =====
PARAM_GRID = [
    {
        "atr": a,
        "rsi": r,
        "macd_fast": f,
        "macd_slow": s,
        "macd_signal": 9,
        "ichimoku_conv": 9,
        "ichimoku_base": 26,
        "ichimoku_span": 52,
    }
    for a in range(10, 21, 2)
    for r in range(10, 21, 2)
    for f in [8, 10, 12]
    for s in [24, 26, 28]
]
