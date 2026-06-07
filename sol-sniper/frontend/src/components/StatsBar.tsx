import type { BotStats } from "../types";

interface Props {
  stats: BotStats;
}

export default function StatsBar({ stats }: Props) {
  const pnlColor = stats.total_pnl_sol >= 0 ? "#00e676" : "#ff1744";

  return (
    <div className="stats-bar">
      <div className="stat-card">
        <span className="stat-label">SOL Balance</span>
        <span className="stat-value">{stats.sol_balance.toFixed(2)} SOL</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Open Positions</span>
        <span className="stat-value">{stats.open_positions}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Total PnL</span>
        <span className="stat-value" style={{ color: pnlColor }}>
          {stats.total_pnl_sol >= 0 ? "+" : ""}
          {stats.total_pnl_sol.toFixed(4)} SOL
        </span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Win Rate</span>
        <span className="stat-value">{stats.win_rate.toFixed(1)}%</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Total Trades</span>
        <span className="stat-value">{stats.total_trades}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Best Trade</span>
        <span className="stat-value" style={{ color: "#00e676" }}>
          +{stats.best_trade_pnl_pct.toFixed(1)}%
        </span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Worst Trade</span>
        <span className="stat-value" style={{ color: "#ff1744" }}>
          {stats.worst_trade_pnl_pct.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
