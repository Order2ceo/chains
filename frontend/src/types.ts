export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorValues {
  timestamp: number;
  ema_200: number | null;
  vwap: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
}

export interface Signal {
  timestamp: number;
  signal_type: "buy" | "sell";
  price: number;
  scenario: string;
  reason: string;
}

export interface StrategyResponse {
  candles: Candle[];
  indicators: IndicatorValues[];
  signals: Signal[];
  trend: "bullish" | "bearish" | "neutral";
  ema_200_15m: number | null;
}
