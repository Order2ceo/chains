import { useEffect, useState } from "react";
import Chart from "./components/Chart";
import SignalPanel from "./components/SignalPanel";
import StatsBar from "./components/StatsBar";
import { fetchStrategyData } from "./api";
import type { StrategyResponse } from "./types";
import "./App.css";

function App() {
  const [data, setData] = useState<StrategyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [numCandles, setNumCandles] = useState(500);

  const loadData = async (candles: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchStrategyData(candles);
      setData(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch strategy data"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(numCandles);
  }, [numCandles]);

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <h1 className="title">VWAPBB Strategy</h1>
          <span className="pair-badge">XAUUSD</span>
          <span className="timeframe-badge">5M</span>
        </div>
        <div className="header-right">
          <select
            className="candle-select"
            value={numCandles}
            onChange={(e) => setNumCandles(Number(e.target.value))}
          >
            <option value={100}>100 Candles</option>
            <option value={200}>200 Candles</option>
            <option value={500}>500 Candles</option>
            <option value={1000}>1000 Candles</option>
          </select>
          <button className="refresh-btn" onClick={() => loadData(numCandles)}>
            Refresh
          </button>
        </div>
      </header>

      {/* Content */}
      {loading && (
        <div className="loading">
          <div className="spinner" />
          <span>Loading strategy data...</span>
        </div>
      )}

      {error && (
        <div className="error">
          <span>Error: {error}</span>
          <button onClick={() => loadData(numCandles)}>Retry</button>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Stats Bar */}
          <section className="stats-section">
            <StatsBar data={data} />
          </section>

          {/* Main Content */}
          <div className="main-content">
            <div className="chart-container">
              <Chart data={data} />
            </div>
            <div className="panel-container">
              <SignalPanel data={data} />
            </div>
          </div>

          {/* Legend */}
          <div className="legend">
            <div className="legend-item">
              <div
                className="legend-color"
                style={{ background: "rgba(33, 150, 243, 0.7)" }}
              />
              <span>Bollinger Bands (20, 2)</span>
            </div>
            <div className="legend-item">
              <div
                className="legend-color"
                style={{ background: "#ff9800" }}
              />
              <span>VWAP</span>
            </div>
            <div className="legend-item">
              <div
                className="legend-color"
                style={{ background: "#e040fb" }}
              />
              <span>EMA 200 (15m)</span>
            </div>
            <div className="legend-item">
              <div
                className="legend-color"
                style={{ background: "#26a69a" }}
              />
              <span>Buy Signal</span>
            </div>
            <div className="legend-item">
              <div
                className="legend-color"
                style={{ background: "#ef5350" }}
              />
              <span>Sell Signal</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default App;
