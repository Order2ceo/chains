import type { StrategyResponse } from "../types";

interface StatsBarProps {
  data: StrategyResponse;
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div
      style={{
        background: "#161b22",
        borderRadius: 8,
        padding: "12px 20px",
        flex: 1,
        minWidth: 140,
      }}
    >
      <div style={{ color: "#8b949e", fontSize: 11, marginBottom: 4 }}>
        {label}
      </div>
      <div
        style={{
          color: color || "#c9d1d9",
          fontSize: 18,
          fontWeight: 700,
        }}
      >
        {value}
      </div>
    </div>
  );
}

export default function StatsBar({ data }: StatsBarProps) {
  const lastCandle = data.candles[data.candles.length - 1];
  const firstCandle = data.candles[0];
  const priceChange = lastCandle.close - firstCandle.open;
  const priceChangePct = (priceChange / firstCandle.open) * 100;

  const buySignals = data.signals.filter((s) => s.signal_type === "buy").length;
  const sellSignals = data.signals.filter(
    (s) => s.signal_type === "sell"
  ).length;

  const lastIndicator = data.indicators[data.indicators.length - 1];

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        flexWrap: "wrap",
      }}
    >
      <StatCard
        label="XAUUSD Price"
        value={`$${lastCandle.close.toFixed(2)}`}
        color={priceChange >= 0 ? "#26a69a" : "#ef5350"}
      />
      <StatCard
        label="Change"
        value={`${priceChange >= 0 ? "+" : ""}${priceChange.toFixed(2)} (${priceChangePct.toFixed(2)}%)`}
        color={priceChange >= 0 ? "#26a69a" : "#ef5350"}
      />
      <StatCard
        label="VWAP"
        value={
          lastIndicator?.vwap !== null
            ? `$${lastIndicator.vwap!.toFixed(2)}`
            : "N/A"
        }
        color="#ff9800"
      />
      <StatCard
        label="Buy Signals"
        value={String(buySignals)}
        color="#26a69a"
      />
      <StatCard
        label="Sell Signals"
        value={String(sellSignals)}
        color="#ef5350"
      />
    </div>
  );
}
