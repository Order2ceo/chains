import type { Position } from "../types";

interface Props {
  positions: Position[];
  onSell: (mint: string) => void;
}

function riskBadge(level: string) {
  const colors: Record<string, string> = {
    safe: "#00e676",
    low: "#69f0ae",
    medium: "#ffd740",
    high: "#ff6e40",
    scam: "#ff1744",
  };
  return (
    <span className="risk-badge" style={{ background: colors[level] || "#666" }}>
      {level.toUpperCase()}
    </span>
  );
}

function statusBadge(status: string) {
  const labels: Record<string, { label: string; color: string }> = {
    open: { label: "OPEN", color: "#00e5ff" },
    closed: { label: "CLOSED", color: "#78909c" },
    stopped_out: { label: "STOPPED", color: "#ff1744" },
    take_profit: { label: "TP HIT", color: "#00e676" },
  };
  const info = labels[status] || { label: status, color: "#666" };
  return (
    <span className="status-badge" style={{ background: info.color }}>
      {info.label}
    </span>
  );
}

export default function Positions({ positions, onSell }: Props) {
  const open = positions.filter((p) => p.status === "open");
  const closed = positions.filter((p) => p.status !== "open");

  return (
    <div className="positions-panel">
      <h3>Active Positions ({open.length})</h3>
      <div className="positions-list">
        {open.length === 0 && (
          <div className="empty-state">No open positions.</div>
        )}
        {open.map((pos) => (
          <div key={pos.id} className="position-card">
            <div className="pos-header">
              <div className="pos-token">
                <strong>{pos.token_symbol}</strong>
                <span className="pos-name">{pos.token_name}</span>
              </div>
              <div className="pos-badges">
                {statusBadge(pos.status)}
                {riskBadge(pos.risk_level)}
              </div>
            </div>
            <div className="pos-details">
              <div className="pos-row">
                <span>Entry</span>
                <span>{pos.entry_price_sol.toExponential(2)} SOL</span>
              </div>
              <div className="pos-row">
                <span>Current</span>
                <span>{pos.current_price_sol.toExponential(2)} SOL</span>
              </div>
              <div className="pos-row">
                <span>Invested</span>
                <span>{pos.invested_sol.toFixed(3)} SOL</span>
              </div>
              <div className="pos-row">
                <span>Value</span>
                <span>{pos.current_value_sol.toFixed(4)} SOL</span>
              </div>
              <div className="pos-row pnl-row">
                <span>PnL</span>
                <span
                  className={pos.pnl_pct >= 0 ? "profit" : "loss"}
                >
                  {pos.pnl_pct >= 0 ? "+" : ""}
                  {pos.pnl_pct.toFixed(1)}% ({pos.pnl_sol >= 0 ? "+" : ""}
                  {pos.pnl_sol.toFixed(4)} SOL)
                </span>
              </div>
            </div>
            <div className="pos-actions">
              <button className="btn-sell" onClick={() => onSell(pos.token_mint)}>
                Sell Now
              </button>
              <a
                className="btn-link"
                href={`https://solscan.io/token/${pos.token_mint}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                View
              </a>
            </div>
          </div>
        ))}
      </div>

      {closed.length > 0 && (
        <>
          <h3 className="closed-header">Closed Positions ({closed.length})</h3>
          <div className="positions-list closed">
            {closed.map((pos) => (
              <div key={pos.id} className="position-card closed-card">
                <div className="pos-header">
                  <div className="pos-token">
                    <strong>{pos.token_symbol}</strong>
                  </div>
                  <div className="pos-badges">
                    {statusBadge(pos.status)}
                    <span
                      className={`pnl-tag ${pos.pnl_pct >= 0 ? "profit" : "loss"}`}
                    >
                      {pos.pnl_pct >= 0 ? "+" : ""}
                      {pos.pnl_pct.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div className="pos-details compact">
                  <span>
                    {pos.invested_sol.toFixed(3)} SOL → {(pos.invested_sol + pos.pnl_sol).toFixed(3)} SOL
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
