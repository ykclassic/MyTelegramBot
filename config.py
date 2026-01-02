import os

# ===== GENERAL =====
APP_NAME = "ProfitForge.....forging maximum profit into your wallets"

# ===== TELEGRAM =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== EXCHANGES =====
SUPPORTED_EXCHANGES = ["binance", "bitget", "gateio", "xt"]

# ===== TRADING =====
TRADING_PAIRS = [
    # Majors from early versions (including previously excluded)
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT", "LTC/USDT",
    # High-volatility & high-volume additions
    "DOGE/USDT", "SHIB/USDT", "PEPE/USDT", "TRX/USDT", "LINK/USDT",
    "TON/USDT", "AVAX/USDT", "DOT/USDT", "MATIC/USDT", "UNI/USDT",
    "AAVE/USDT", "NEAR/USDT", "SUI/USDT"
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
