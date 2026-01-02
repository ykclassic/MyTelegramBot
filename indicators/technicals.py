import pandas as pd
import numpy as np

def rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def macd(df, fast=12, slow=26, signal=9):
    exp1 = df["close"].ewm(span=fast, adjust=False).mean()
    exp2 = df["close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    return df

def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(period).mean()
    return df

def ichimoku(df, conv=9, base=26, span=52):
    high_conv = df["high"].rolling(conv).max()
    low_conv = df["low"].rolling(conv).min()
    df["Conversion"] = (high_conv + low_conv) / 2

    high_base = df["high"].rolling(base).max()
    low_base = df["low"].rolling(base).min()
    df["Base"] = (high_base + low_base) / 2

    df["SpanA"] = ((df["Conversion"] + df["Base"]) / 2).shift(base)
    df["SpanB"] = ((df["high"].rolling(span).max() + df["low"].rolling(span).min()) / 2).shift(base)

    return df
