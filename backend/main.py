from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import Candle, IndicatorValues, StrategyResponse, Trend
from indicators import calculate_ema, calculate_bollinger_bands, calculate_vwap
from strategy import determine_trend, generate_signals
from data_provider import generate_simulated_xauusd, resample_to_15m

app = FastAPI(
    title="VWAPBB Strategy – XAUUSD",
    description="Full-stack VWAP + Bollinger Bands trading strategy for XAUUSD",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/strategy", response_model=StrategyResponse)
def get_strategy_data(num_candles: int = 500):
    """
    Generate XAUUSD data with all indicators and trading signals.
    Returns candles, indicator overlays, and buy/sell signals.
    """
    # Generate 5-minute candle data
    df_5m = generate_simulated_xauusd(num_candles=num_candles)

    # Resample to 15-minute for EMA 200 trend filter
    df_15m = resample_to_15m(df_5m)
    ema_200_15m_series = calculate_ema(df_15m["close"], 200)
    ema_200_15m_value = float(ema_200_15m_series.iloc[-1]) if len(ema_200_15m_series) > 0 else None

    # Calculate indicators on 5-minute data
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df_5m["close"])
    vwap = calculate_vwap(df_5m)

    # Determine current trend
    current_price = float(df_5m["close"].iloc[-1])
    trend = determine_trend(ema_200_15m_value or 0, current_price)

    # Generate signals
    signals = generate_signals(df_5m, ema_200_15m_value or 0)

    # Build response
    candles = [
        Candle(
            timestamp=int(row["timestamp"]),
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
        )
        for _, row in df_5m.iterrows()
    ]

    indicators = []
    for i, row in df_5m.iterrows():
        idx = int(i) if not isinstance(i, int) else i
        indicators.append(
            IndicatorValues(
                timestamp=int(row["timestamp"]),
                ema_200=ema_200_15m_value,
                vwap=float(vwap.iloc[idx]) if idx < len(vwap) and not vwap.isna().iloc[idx] else None,
                bb_upper=float(bb_upper.iloc[idx]) if idx < len(bb_upper) and not bb_upper.isna().iloc[idx] else None,
                bb_middle=float(bb_middle.iloc[idx]) if idx < len(bb_middle) and not bb_middle.isna().iloc[idx] else None,
                bb_lower=float(bb_lower.iloc[idx]) if idx < len(bb_lower) and not bb_lower.isna().iloc[idx] else None,
            )
        )

    return StrategyResponse(
        candles=candles,
        indicators=indicators,
        signals=signals,
        trend=trend,
        ema_200_15m=ema_200_15m_value,
    )


@app.get("/api/health")
def health_check():
    return {"status": "ok", "strategy": "VWAPBB", "pair": "XAUUSD"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
