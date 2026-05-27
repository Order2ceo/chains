import numpy as np
import pandas as pd


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_bollinger_bands(
    series: pd.Series, period: int = 20, std_dev: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands (upper, middle, lower)."""
    middle = series.rolling(window=period).mean()
    rolling_std = series.rolling(window=period).std()
    upper = middle + (rolling_std * std_dev)
    lower = middle - (rolling_std * std_dev)
    return upper, middle, lower


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume Weighted Average Price.
    Resets at the start of each trading day.
    """
    df = df.copy()
    df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3.0
    df["tp_volume"] = df["typical_price"] * df["volume"]

    df["date"] = pd.to_datetime(df["timestamp"], unit="s").dt.date

    vwap_values = []
    for _, group in df.groupby("date"):
        cum_tp_vol = group["tp_volume"].cumsum()
        cum_vol = group["volume"].cumsum()
        vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
        vwap_values.append(vwap)

    if vwap_values:
        return pd.concat(vwap_values).sort_index()
    return pd.Series(dtype=float)


def is_bullish_engulfing(
    prev_open: float,
    prev_close: float,
    curr_open: float,
    curr_close: float,
) -> bool:
    """Detect bullish engulfing candlestick pattern."""
    prev_bearish = prev_close < prev_open
    curr_bullish = curr_close > curr_open
    engulfs = curr_open <= prev_close and curr_close >= prev_open
    return prev_bearish and curr_bullish and engulfs


def is_bearish_engulfing(
    prev_open: float,
    prev_close: float,
    curr_open: float,
    curr_close: float,
) -> bool:
    """Detect bearish engulfing candlestick pattern."""
    prev_bullish = prev_close > prev_open
    curr_bearish = curr_close < curr_open
    engulfs = curr_open >= prev_close and curr_close <= prev_open
    return prev_bullish and curr_bearish and engulfs


def is_near(price: float, level: float, threshold_pct: float = 0.001) -> bool:
    """Check if price is near a given level within a percentage threshold."""
    if level == 0:
        return False
    return abs(price - level) / level <= threshold_pct
