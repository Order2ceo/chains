import type { TokenInfo } from "../types";

interface Props {
  tokens: TokenInfo[];
  onBuy: (mint: string) => void;
}

function platformBadge(platform: string) {
  const colors: Record<string, string> = {
    pumpfun: "#00e5ff",
    raydium: "#7c4dff",
    jupiter: "#ff9100",
    orca: "#00bfa5",
  };
  return (
    <span className="platform-badge" style={{ background: colors[platform] || "#666" }}>
      {platform.toUpperCase()}
    </span>
  );
}

function formatAge(detectedAt: string): string {
  const diff = Date.now() - new Date(detectedAt).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

function formatMcap(usd: number): string {
  if (usd >= 1_000_000) return `$${(usd / 1_000_000).toFixed(1)}M`;
  if (usd >= 1_000) return `$${(usd / 1_000).toFixed(1)}K`;
  return `$${usd.toFixed(0)}`;
}

export default function TokenFeed({ tokens, onBuy }: Props) {
  return (
    <div className="token-feed">
      <h3>
        <span className="pulse-dot" /> New Tokens Detected
      </h3>
      <div className="token-list">
        {tokens.length === 0 && (
          <div className="empty-state">No tokens detected yet. Start the scanner to begin.</div>
        )}
        {tokens.map((token) => (
          <div key={token.mint} className="token-card">
            <div className="token-header">
              <div className="token-name">
                <strong>{token.symbol}</strong>
                <span className="token-fullname">{token.name}</span>
              </div>
              <div className="token-meta">
                {platformBadge(token.platform)}
                <span className="token-age">{formatAge(token.detected_at)}</span>
              </div>
            </div>
            <div className="token-stats">
              <div className="token-stat">
                <span className="label">Liquidity</span>
                <span className="value">{token.initial_liquidity_sol.toFixed(1)} SOL</span>
              </div>
              <div className="token-stat">
                <span className="label">MCap</span>
                <span className="value">{formatMcap(token.market_cap_usd)}</span>
              </div>
              <div className="token-stat">
                <span className="label">Holders</span>
                <span className="value">{token.holder_count.toLocaleString()}</span>
              </div>
            </div>
            <div className="token-actions">
              <button className="btn-buy" onClick={() => onBuy(token.mint)}>
                Snipe
              </button>
              <a
                className="btn-link"
                href={`https://solscan.io/token/${token.mint}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Solscan
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
