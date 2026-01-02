from signals.generator import generate_signal

def backtest(df, params):
    trades = []
    position = None

    for i in range(60, len(df)):
        sub = df.iloc[:i]
        signal, _, levels = generate_signal(sub, params)
        price = df.iloc[i]["Close"]

        if position is None and "BUY" in signal:
            position = levels

        if position:
            if price <= position["sl"] or price >= position["tp2"]:
                trades.append(price - position["entry"])
                position = None

    if not trades:
        return {"total_trades": 0, "win_rate": 0, "avg_pl": 0, "total_pl": 0}

    return {
        "total_trades": len(trades),
        "win_rate": sum(t > 0 for t in trades) / len(trades) * 100,
        "avg_pl": sum(trades) / len(trades),
        "total_pl": sum(trades)
    }
