import type { Signal, StrategyResponse } from "../types";

interface SignalPanelProps {
  data: StrategyResponse;
}

function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString();
}

function SignalCard({ signal }: { signal: Signal }) {
  const isBuy = signal.signal_type === "buy";
  return (
    <div
      style={{
        background: isBuy
          ? "rgba(38, 166, 154, 0.1)"
          : "rgba(239, 83, 80, 0.1)",
        border: `1px solid ${isBuy ? "#26a69a" : "#ef5350"}`,
        borderRadius: 8,
        padding: "12px 16px",
        marginBottom: 8,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 4,
        }}
      >
        <span
          style={{
            fontWeight: 700,
            color: isBuy ? "#26a69a" : "#ef5350",
            fontSize: 14,
          }}
        >
          {signal.signal_type.toUpperCase()} @ ${signal.price.toFixed(2)}
        </span>
        <span style={{ color: "#8b949e", fontSize: 12 }}>
          {signal.scenario}
        </span>
      </div>
      <div style={{ color: "#c9d1d9", fontSize: 12 }}>{signal.reason}</div>
      <div style={{ color: "#8b949e", fontSize: 11, marginTop: 4 }}>
        {formatTime(signal.timestamp)}
      </div>
    </div>
  );
}

export default function SignalPanel({ data }: SignalPanelProps) {
  const trendColor =
    data.trend === "bullish"
      ? "#26a69a"
      : data.trend === "bearish"
        ? "#ef5350"
        : "#8b949e";

  return (
    <div
      style={{
        background: "#161b22",
        borderRadius: 12,
        padding: 20,
        height: "100%",
      }}
    >
      {/* Trend Status */}
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ color: "#c9d1d9", margin: "0 0 8px 0", fontSize: 14 }}>
          Market Trend (EMA 200 · 15m)
        </h3>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: trendColor,
            }}
          />
          <span
            style={{ color: trendColor, fontWeight: 700, fontSize: 18 }}
          >
            {data.trend.toUpperCase()}
          </span>
        </div>
        {data.ema_200_15m !== null && (
          <div style={{ color: "#8b949e", fontSize: 12, marginTop: 4 }}>
            EMA 200 (15m): ${data.ema_200_15m.toFixed(2)}
          </div>
        )}
      </div>

      {/* Strategy Info */}
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ color: "#c9d1d9", margin: "0 0 8px 0", fontSize: 14 }}>
          Strategy Rules
        </h3>
        <div style={{ color: "#8b949e", fontSize: 12, lineHeight: 1.6 }}>
          {data.trend === "bullish" ? (
            <>
              <div>• Only BUY signals active</div>
              <div>• Price must be above EMA 200</div>
              <div>• Look for touches on VWAP or Lower BB</div>
              <div>• Bullish engulfing pattern required</div>
            </>
          ) : data.trend === "bearish" ? (
            <>
              <div>• Only SELL signals active</div>
              <div>• Price must be below EMA 200</div>
              <div>• Look for touches on VWAP or Upper BB</div>
              <div>• Bearish engulfing pattern required</div>
            </>
          ) : (
            <div>• No clear trend — no signals generated</div>
          )}
        </div>
      </div>

      {/* Signals */}
      <div>
        <h3 style={{ color: "#c9d1d9", margin: "0 0 12px 0", fontSize: 14 }}>
          Signals ({data.signals.length})
        </h3>
        <div
          style={{
            maxHeight: 300,
            overflowY: "auto",
          }}
        >
          {data.signals.length === 0 ? (
            <div style={{ color: "#8b949e", fontSize: 13 }}>
              No signals detected in the current data window.
            </div>
          ) : (
            [...data.signals]
              .reverse()
              .map((signal, i) => <SignalCard key={i} signal={signal} />)
          )}
        </div>
      </div>
    </div>
  );
}
