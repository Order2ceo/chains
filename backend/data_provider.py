import time
import numpy as np
import pandas as pd


def generate_simulated_xauusd(
    num_candles: int = 500,
    timeframe_seconds: int = 300,
    base_price: float = 2650.0,
) -> pd.DataFrame:
    """
    Generate simulated XAUUSD OHLCV data for demonstration.
    Produces realistic gold price movements with trends and volatility.
    """
    np.random.seed(42)

    end_time = int(time.time())
    end_time = end_time - (end_time % timeframe_seconds)
    timestamps = [end_time - (num_candles - 1 - i) * timeframe_seconds for i in range(num_candles)]

    prices = [base_price]
    volatility = 0.0008  # ~0.08% per 5-min candle for gold

    # Add a slow trend component
    trend = np.sin(np.linspace(0, 4 * np.pi, num_candles)) * 15

    for i in range(1, num_candles):
        change = np.random.normal(0, volatility) * prices[-1]
        trend_component = (trend[i] - trend[i - 1])
        new_price = prices[-1] + change + trend_component
        prices.append(max(new_price, base_price * 0.95))

    candles = []
    for i in range(num_candles):
        p = prices[i]
        spread = p * np.random.uniform(0.0002, 0.001)

        o = p + np.random.normal(0, spread * 0.3)
        c = p + np.random.normal(0, spread * 0.3)

        h = max(o, c) + abs(np.random.normal(0, spread * 0.5))
        l = min(o, c) - abs(np.random.normal(0, spread * 0.5))

        vol = np.random.uniform(100, 5000)

        candles.append({
            "timestamp": timestamps[i],
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
            "volume": round(vol, 2),
        })

    return pd.DataFrame(candles)


def resample_to_15m(df_5m: pd.DataFrame) -> pd.DataFrame:
    """Resample 5-minute candles to 15-minute candles."""
    df = df_5m.copy()
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df.set_index("datetime")

    resampled = df.resample("15min").agg({
        "timestamp": "first",
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna()

    return resampled.reset_index(drop=True)
