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
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",  # Your originals (add any others you have)
    # New 13 based on volatility/volume
    "DOGE/USDT", "TRX/USDT", "LINK/USDT", "AVAX/USDT", "TON/USDT",
    "DOT/USDT", "MATIC/USDT", "SHIB/USDT", "UNI/USDT", "AAVE/USDT",
    "NEAR/USDT", "HBAR/USDT", "SUI/USDT"
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
