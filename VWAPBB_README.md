# VWAPBB Strategy – XAUUSD

A full-stack trading strategy application implementing the VWAP + Bollinger Bands (VWAPBB) strategy for XAUUSD on the 5-minute timeframe.

## Strategy Overview

### Indicators
- **Bollinger Bands (BB)** – 20-period, 2 standard deviations on the 5-minute chart
- **EMA 200** – Calculated on the 15-minute timeframe for trend filtering
- **VWAP** – Volume Weighted Average Price, resetting daily

### Trend Filter
The EMA 200 on the 15-minute timeframe determines the overall market trend:
- **Bullish**: Price above EMA 200 → only BUY signals
- **Bearish**: Price below EMA 200 → only SELL signals

### Buy Conditions (Bullish Trend)

**Scenario 1**: Price above EMA 200 AND above VWAP
- Price touches/approaches VWAP or Lower Bollinger Band
- Bullish engulfing pattern appears → Enter at candle close

**Scenario 2**: Price above EMA 200 but below VWAP
- Price touches/approaches Lower Bollinger Band
- Bullish engulfing pattern appears → Enter at candle close

### Sell Conditions (Bearish Trend)
- Price below EMA 200
- Price touches/approaches VWAP or Upper Bollinger Band
- Bearish engulfing pattern appears → Enter at candle close

## Tech Stack

### Backend
- **Python 3.12** + **FastAPI**
- **pandas** / **numpy** for indicator calculations
- Simulated XAUUSD data generation

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Lightweight Charts** (TradingView) for interactive charting
- Dark theme with responsive design

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
The API will be available at `http://localhost:8000`.

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be available at `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategy?num_candles=500` | Get candles, indicators, and signals |
| GET | `/api/health` | Health check |
| GET | `/docs` | Interactive API documentation (Swagger) |
