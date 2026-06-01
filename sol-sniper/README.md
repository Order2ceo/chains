# SOL Meme Coin Sniper Bot

Full-stack Solana meme coin sniper bot with auto-trading, rug-pull detection, and a real-time dashboard.

## Features

- **Token Scanner**: Real-time detection of new token launches on Pump.fun, Raydium, and Jupiter
- **Rug-Pull Analyzer**: Security scoring based on mint authority, freeze authority, holder concentration, liquidity locks
- **Auto-Trading Engine**: Configurable auto-buy on detection, auto-sell with take-profit, stop-loss, and trailing stop
- **Dashboard**: Live token feed, active positions with P&L, trade history, and bot configuration
- **Safety Filters**: Min liquidity, max token age, holder concentration limits, locked liquidity requirements

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Solana RPC, aiohttp, WebSocket, SQLite
- **Frontend**: React 18, TypeScript, Vite

## Quick Start

### Backend
```bash
cd sol-sniper/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
Backend runs at http://localhost:8001

### Frontend
```bash
cd sol-sniper/frontend
npm install
npm run dev
```
Frontend runs at http://localhost:5173

## Configuration

Set environment variables or use the Settings panel in the dashboard:

| Variable | Default | Description |
|----------|---------|-------------|
| `SOLANA_RPC_URL` | mainnet-beta | Solana RPC endpoint (Helius, QuickNode recommended) |
| `BUY_AMOUNT_SOL` | 0.1 | SOL amount per trade |
| `TAKE_PROFIT_PCT` | 100 | Take profit percentage |
| `STOP_LOSS_PCT` | 30 | Stop loss percentage |
| `AUTO_BUY_ENABLED` | false | Enable automatic buying |
| `AUTO_SELL_ENABLED` | true | Enable TP/SL auto-sell |

## Architecture

```
sol-sniper/
├── backend/
│   ├── main.py          # FastAPI app + WebSocket + REST endpoints
│   ├── config.py        # Bot configuration + Solana program IDs
│   ├── models.py        # Pydantic models
│   ├── scanner.py       # Token scanner (Pump.fun, Raydium, Jupiter)
│   ├── analyzer.py      # Rug-pull detection + risk scoring
│   ├── trader.py        # Auto-trading engine (buy/sell/TP/SL)
│   ├── database.py      # SQLite trade/position storage
│   └── ws_manager.py    # WebSocket connection manager
└── frontend/
    └── src/
        ├── App.tsx              # Main app with tabs
        ├── api.ts               # API client
        ├── types.ts             # TypeScript interfaces
        └── components/
            ├── StatsBar.tsx     # Bot statistics
            ├── TokenFeed.tsx    # New token feed
            ├── Positions.tsx    # Active/closed positions
            └── Settings.tsx     # Bot configuration
```

## Disclaimer

This bot is for educational purposes. Trading meme coins is extremely risky. Use at your own risk. This is not financial advice.
