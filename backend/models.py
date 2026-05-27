from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Trend(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Candle(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class IndicatorValues(BaseModel):
    timestamp: int
    ema_200: Optional[float] = None
    vwap: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None


class Signal(BaseModel):
    timestamp: int
    signal_type: SignalType
    price: float
    scenario: str
    reason: str


class StrategyResponse(BaseModel):
    candles: list[Candle]
    indicators: list[IndicatorValues]
    signals: list[Signal]
    trend: Trend
    ema_200_15m: Optional[float] = None
