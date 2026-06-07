import { useState } from "react";
import type { BotConfig } from "../types";
import { updateConfig } from "../api";

interface Props {
  config: BotConfig | null;
  onRefresh: () => void;
}

export default function Settings({ config, onRefresh }: Props) {
  const [saving, setSaving] = useState(false);
  const [localConfig, setLocalConfig] = useState<Partial<BotConfig>>({});

  if (!config) return <div className="settings-panel">Loading config...</div>;

  const merged = { ...config, ...localConfig };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateConfig(localConfig);
      setLocalConfig({});
      onRefresh();
    } catch (err) {
      console.error("Failed to save config", err);
    } finally {
      setSaving(false);
    }
  };

  const update = (key: keyof BotConfig, value: number | boolean | string[]) => {
    setLocalConfig((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="settings-panel">
      <h3>Bot Settings</h3>

      <div className="settings-group">
        <h4>Trading Parameters</h4>
        <div className="setting-row">
          <label>Buy Amount (SOL)</label>
          <input
            type="number"
            step="0.01"
            value={merged.buy_amount_sol}
            onChange={(e) => update("buy_amount_sol", parseFloat(e.target.value))}
          />
        </div>
        <div className="setting-row">
          <label>Slippage (bps)</label>
          <input
            type="number"
            step="50"
            value={merged.slippage_bps}
            onChange={(e) => update("slippage_bps", parseInt(e.target.value))}
          />
        </div>
        <div className="setting-row">
          <label>Max Concurrent Positions</label>
          <input
            type="number"
            step="1"
            value={merged.max_concurrent_positions}
            onChange={(e) =>
              update("max_concurrent_positions", parseInt(e.target.value))
            }
          />
        </div>
      </div>

      <div className="settings-group">
        <h4>Take-Profit / Stop-Loss</h4>
        <div className="setting-row">
          <label>Take Profit (%)</label>
          <input
            type="number"
            step="5"
            value={merged.take_profit_pct}
            onChange={(e) => update("take_profit_pct", parseFloat(e.target.value))}
          />
        </div>
        <div className="setting-row">
          <label>Stop Loss (%)</label>
          <input
            type="number"
            step="5"
            value={merged.stop_loss_pct}
            onChange={(e) => update("stop_loss_pct", parseFloat(e.target.value))}
          />
        </div>
        <div className="setting-row">
          <label>Trailing Stop (%)</label>
          <input
            type="number"
            step="5"
            value={merged.trailing_stop_pct}
            onChange={(e) => update("trailing_stop_pct", parseFloat(e.target.value))}
          />
        </div>
      </div>

      <div className="settings-group">
        <h4>Safety Filters</h4>
        <div className="setting-row">
          <label>Min Liquidity (SOL)</label>
          <input
            type="number"
            step="1"
            value={merged.min_liquidity_sol}
            onChange={(e) => update("min_liquidity_sol", parseFloat(e.target.value))}
          />
        </div>
        <div className="setting-row">
          <label>Max Token Age (seconds)</label>
          <input
            type="number"
            step="60"
            value={merged.max_token_age_seconds}
            onChange={(e) =>
              update("max_token_age_seconds", parseInt(e.target.value))
            }
          />
        </div>
        <div className="setting-row">
          <label>Max Top Holder (%)</label>
          <input
            type="number"
            step="5"
            value={merged.max_top_holder_pct}
            onChange={(e) =>
              update("max_top_holder_pct", parseFloat(e.target.value))
            }
          />
        </div>
        <div className="setting-row">
          <label>Max Top 10 Holders (%)</label>
          <input
            type="number"
            step="1"
            value={merged.max_top10_holder_pct}
            onChange={(e) =>
              update("max_top10_holder_pct", parseFloat(e.target.value))
            }
          />
        </div>
        <div className="setting-row">
          <label>Min Liquidity (USD)</label>
          <input
            type="number"
            step="1000"
            value={merged.min_liquidity_usd}
            onChange={(e) =>
              update("min_liquidity_usd", parseFloat(e.target.value))
            }
          />
        </div>
        <div className="setting-row">
          <label>Max Total Supply</label>
          <input
            type="number"
            step="1000000"
            value={merged.max_total_supply}
            onChange={(e) =>
              update("max_total_supply", parseFloat(e.target.value))
            }
          />
        </div>
        <div className="setting-row toggle-row">
          <label>Require Locked Liquidity</label>
          <input
            type="checkbox"
            checked={merged.require_locked_liquidity}
            onChange={(e) => update("require_locked_liquidity", e.target.checked)}
          />
        </div>
        <div className="setting-row toggle-row">
          <label>Require Renounced Mint</label>
          <input
            type="checkbox"
            checked={merged.require_renounced_mint}
            onChange={(e) => update("require_renounced_mint", e.target.checked)}
          />
        </div>
        <div className="setting-row toggle-row">
          <label>Require No Freeze Authority</label>
          <input
            type="checkbox"
            checked={merged.require_no_freeze}
            onChange={(e) => update("require_no_freeze", e.target.checked)}
          />
        </div>
      </div>

      <div className="settings-group">
        <h4>Automation</h4>
        <div className="setting-row toggle-row">
          <label>Auto-Buy Enabled</label>
          <input
            type="checkbox"
            checked={merged.auto_buy_enabled}
            onChange={(e) => update("auto_buy_enabled", e.target.checked)}
          />
        </div>
        <div className="setting-row toggle-row">
          <label>Auto-Sell (TP/SL) Enabled</label>
          <input
            type="checkbox"
            checked={merged.auto_sell_enabled}
            onChange={(e) => update("auto_sell_enabled", e.target.checked)}
          />
        </div>
      </div>

      <button
        className="btn-save"
        onClick={handleSave}
        disabled={saving || Object.keys(localConfig).length === 0}
      >
        {saving ? "Saving..." : "Save Settings"}
      </button>
    </div>
  );
}
