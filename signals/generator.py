from indicators.technicals import rsi, macd, atr, ichimoku

def generate_signal(df, params):
    df = atr(df, params["atr"])
    df = rsi(df, params["rsi"])
    df = macd(df, params["macd_fast"], params["macd_slow"], params["macd_signal"])
    df = ichimoku(df, params["ichimoku_conv"], params["ichimoku_base"], params["ichimoku_span"])

    last = df.iloc[-1]
    score = 50

    if last["RSI"] < 30: score += 20
    if last["RSI"] > 70: score -= 20
    if last["MACD"] > last["MACD_Signal"]: score += 15
    if last["MACD"] < last["MACD_Signal"]: score -= 15

    cloud_top = max(last["SpanA"], last["SpanB"])
    cloud_bottom = min(last["SpanA"], last["SpanB"])

    if last["close"] > cloud_top: score += 15
    if last["close"] < cloud_bottom: score -= 15

    if score >= 80: signal = "STRONG BUY"
    elif score >= 65: signal = "BUY"
    elif score <= 20: signal = "STRONG SELL"
    elif score <= 35: signal = "SELL"
    else: signal = "HOLD"

    entry = last["close"]
    atr_val = last["ATR"]

    return signal, score, {
        "entry": entry,
        "sl": entry - atr_val * 2 if "BUY" in signal else entry + atr_val * 2,
        "tp1": entry * 1.03 if "BUY" in signal else entry * 0.97,
        "tp2": entry * 1.06 if "BUY" in signal else entry * 0.94,
    }
