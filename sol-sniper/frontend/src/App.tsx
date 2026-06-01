import { useEffect, useState, useCallback } from "react";
import StatsBar from "./components/StatsBar";
import TokenFeed from "./components/TokenFeed";
import Positions from "./components/Positions";
import Settings from "./components/Settings";
import {
  fetchDashboard,
  fetchConfig,
  manualBuy,
  manualSell,
  startScanner,
  stopScanner,
} from "./api";
import type { BotConfig, DashboardData } from "./types";
import "./App.css";

type Tab = "dashboard" | "tokens" | "positions" | "settings";

function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [config, setConfig] = useState<BotConfig | null>(null);
  const [tab, setTab] = useState<Tab>("dashboard");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scannerActive, setScannerActive] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [dashData, cfgData] = await Promise.all([
        fetchDashboard(),
        fetchConfig(),
      ]);
      setData(dashData);
      setConfig(cfgData);
      setScannerActive(dashData.scanner_active);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleBuy = async (mint: string) => {
    try {
      await manualBuy(mint);
      await loadData();
    } catch (err) {
      console.error("Buy failed:", err);
    }
  };

  const handleSell = async (mint: string) => {
    try {
      await manualSell(mint);
      await loadData();
    } catch (err) {
      console.error("Sell failed:", err);
    }
  };

  const toggleScanner = async () => {
    try {
      if (scannerActive) {
        await stopScanner();
      } else {
        await startScanner();
      }
      setScannerActive(!scannerActive);
      await loadData();
    } catch (err) {
      console.error("Scanner toggle failed:", err);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1 className="title">
            <span className="sol-icon">◎</span> SOL Sniper Bot
          </h1>
          <span className="version-badge">v1.0</span>
        </div>
        <div className="header-right">
          <div className={`scanner-status ${scannerActive ? "active" : ""}`}>
            <span className={`status-dot ${scannerActive ? "green" : "red"}`} />
            {scannerActive ? "Scanner Active" : "Scanner Idle"}
          </div>
          <button
            className={`scanner-btn ${scannerActive ? "stop" : "start"}`}
            onClick={toggleScanner}
          >
            {scannerActive ? "Stop Scanner" : "Start Scanner"}
          </button>
          <button className="refresh-btn" onClick={loadData}>
            Refresh
          </button>
        </div>
      </header>

      <nav className="tabs">
        {(["dashboard", "tokens", "positions", "settings"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t === "dashboard" && "Dashboard"}
            {t === "tokens" && `Tokens (${data?.recent_tokens.length ?? 0})`}
            {t === "positions" && `Positions (${data?.positions.filter((p) => p.status === "open").length ?? 0})`}
            {t === "settings" && "Settings"}
          </button>
        ))}
      </nav>

      {loading && (
        <div className="loading">
          <div className="spinner" />
          <span>Connecting to sniper bot...</span>
        </div>
      )}

      {error && (
        <div className="error">
          <span>Error: {error}</span>
          <button onClick={loadData}>Retry</button>
        </div>
      )}

      {data && !loading && (
        <main className="main-content">
          {tab === "dashboard" && (
            <>
              <StatsBar stats={data.stats} />
              <div className="dashboard-grid">
                <div className="grid-left">
                  <TokenFeed
                    tokens={data.recent_tokens.slice(0, 8)}
                    onBuy={handleBuy}
                  />
                </div>
                <div className="grid-right">
                  <Positions
                    positions={data.positions}
                    onSell={handleSell}
                  />
                </div>
              </div>
            </>
          )}
          {tab === "tokens" && (
            <TokenFeed tokens={data.recent_tokens} onBuy={handleBuy} />
          )}
          {tab === "positions" && (
            <Positions positions={data.positions} onSell={handleSell} />
          )}
          {tab === "settings" && (
            <Settings config={config} onRefresh={loadData} />
          )}
        </main>
      )}

      <footer className="footer">
        <span>SOL Meme Coin Sniper Bot — Use at your own risk. Not financial advice.</span>
        <span>Platforms: Pump.fun · Raydium · Jupiter</span>
      </footer>
    </div>
  );
}

export default App;
