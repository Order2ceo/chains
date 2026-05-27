import pandas as pd

from models import Trend, SignalType, Signal
from indicators import (
    calculate_ema,
    calculate_bollinger_bands,
    calculate_vwap,
    is_bullish_engulfing,
    is_bearish_engulfing,
    is_near,
)


NEAR_THRESHOLD = 0.0015  # 0.15% proximity threshold for XAUUSD


def determine_trend(ema_200_value: float, current_price: float) -> Trend:
    """Determine trend based on price relative to EMA 200 from 15m timeframe."""
    if pd.isna(ema_200_value):
        return Trend.NEUTRAL
    if current_price > ema_200_value:
        return Trend.BULLISH
    elif current_price < ema_200_value:
        return Trend.BEARISH
    return Trend.NEUTRAL


def generate_signals(
    df_5m: pd.DataFrame,
    ema_200_15m_value: float,
) -> list[Signal]:
    """
    Generate buy/sell signals based on the VWAPBB strategy.

    Parameters:
        df_5m: DataFrame with 5-minute OHLCV candles
        ema_200_15m_value: Current EMA 200 value from 15-minute timeframe
    """
    if len(df_5m) < 21:
        return []

    df = df_5m.copy()

    # Calculate indicators on 5m data
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df["close"])
    vwap = calculate_vwap(df)

    df["bb_upper"] = bb_upper
    df["bb_middle"] = bb_middle
    df["bb_lower"] = bb_lower
    df["vwap"] = vwap

    signals: list[Signal] = []

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]

        price = row["close"]
        trend = determine_trend(ema_200_15m_value, price)

        if trend == Trend.NEUTRAL:
            continue

        if pd.isna(row["bb_lower"]) or pd.isna(row["bb_upper"]) or pd.isna(row["vwap"]):
            continue

        # --- BUY CONDITIONS (Bullish Trend) ---
        if trend == Trend.BULLISH:
            if not is_bullish_engulfing(
                prev["open"], prev["close"], row["open"], row["close"]
            ):
                continue

            # Scenario 1: Price above VWAP, touches VWAP or lower BB
            if price > row["vwap"]:
                near_vwap = is_near(row["low"], row["vwap"], NEAR_THRESHOLD)
                near_lower_bb = is_near(row["low"], row["bb_lower"], NEAR_THRESHOLD)
                if near_vwap or near_lower_bb:
                    trigger = "VWAP" if near_vwap else "Lower BB"
                    signals.append(
                        Signal(
                            timestamp=int(row["timestamp"]),
                            signal_type=SignalType.BUY,
                            price=price,
                            scenario="Buy Scenario 1",
                            reason=(
                                f"Bullish engulfing above EMA200 & VWAP. "
                                f"Price touched {trigger}."
                            ),
                        )
                    )

            # Scenario 2: Price below VWAP but above EMA200, touches lower BB
            else:
                near_lower_bb = is_near(row["low"], row["bb_lower"], NEAR_THRESHOLD)
                if near_lower_bb:
                    signals.append(
                        Signal(
                            timestamp=int(row["timestamp"]),
                            signal_type=SignalType.BUY,
                            price=price,
                            scenario="Buy Scenario 2",
                            reason=(
                                "Bullish engulfing above EMA200, below VWAP. "
                                "Price touched Lower BB."
                            ),
                        )
                    )

        # --- SELL CONDITIONS (Bearish Trend) ---
        elif trend == Trend.BEARISH:
            if not is_bearish_engulfing(
                prev["open"], prev["close"], row["open"], row["close"]
            ):
                continue

            near_vwap = is_near(row["high"], row["vwap"], NEAR_THRESHOLD)
            near_upper_bb = is_near(row["high"], row["bb_upper"], NEAR_THRESHOLD)

            if near_vwap or near_upper_bb:
                trigger = "VWAP" if near_vwap else "Upper BB"
                signals.append(
                    Signal(
                        timestamp=int(row["timestamp"]),
                        signal_type=SignalType.SELL,
                        price=price,
                        scenario="Sell Scenario",
                        reason=(
                            f"Bearish engulfing below EMA200. "
                            f"Price touched {trigger}."
                        ),
                    )
                )

    return signals
