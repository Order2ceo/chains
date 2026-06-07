# SOL Meme Coin Sniper Bot

Full-stack Solana meme coin sniper bot with auto-trading, rug-pull detection, and a real-time dashboard.

## Features

- **Token Scanner**: Real-time detection of new token launches on Pump.fun, Raydium, and Jupiter
- **Rug-Pull Analyzer**: Security scoring based on mint authority, freeze authority, holder concentration, liquidity locks
- **Auto-Trading Engine**: Configurable auto-buy on detection, auto-sell with take-profit, stop-loss, and trailing stop
- **Live on-chain trading**: Real SOL↔token swaps via the Jupiter aggregator, signed by a server-side wallet — gated behind an explicit Dry-Run/LIVE toggle
- **Dashboard**: Live token feed, active positions with P&L, trade history, wallet status, and bot configuration
- **Safety Filters**: Min liquidity, max token age, holder concentration limits, locked liquidity requirements

## Dry-Run vs. Live trading

The bot starts in **Dry-Run** mode (safe default): it uses real market prices and real new-token feeds, but **never sends a transaction**. Buys/sells are simulated locally so you can watch the strategy without risking funds.

To trade real funds you must do **both**:

1. Provide a wallet + RPC (see Configuration below), and
2. Click the **Dry-Run → LIVE** toggle in the dashboard header (a confirmation dialog warns you first). Live mode cannot be enabled unless a wallet is loaded.

In LIVE mode, buys swap SOL→token and sells swap the wallet's full token balance back to SOL, both routed through Jupiter with your configured slippage and priority fee.

> ⚠️ **No bot can guarantee profit.** Meme-coin trading is extremely risky — most new tokens go to zero. Use a dedicated burner wallet funded with only what you can afford to lose. There is no "95% gain" — that is not real.

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
| `SOLANA_RPC_URL` | mainnet-beta | Solana RPC endpoint (Helius, QuickNode recommended; free public RPC is too slow for sniping) |
| `SOLANA_WALLET_PRIVATE_KEY` | _(none)_ | Base58 private key of the signing wallet. **Use a dedicated burner wallet.** Leave unset to stay read-only/dry-run |
| `LIVE_MODE` | false | Start in live mode. Even if `true`, live trading only activates when a wallet is loaded. Can also be toggled at runtime in the UI |
| `BUY_AMOUNT_SOL` | 0.1 | SOL amount per trade |
| `TAKE_PROFIT_PCT` | 100 | Take profit percentage |
| `STOP_LOSS_PCT` | 30 | Stop loss percentage |
| `AUTO_BUY_ENABLED` | false | Enable automatic buying |
| `AUTO_SELL_ENABLED` | true | Enable TP/SL auto-sell |
| `SCANNER_AUTOSTART` | false | Start the scanner automatically on boot (for 24/7 hosting) |

Never commit your private key. Pass it via the environment (e.g. a local `.env` file that is git-ignored):
```bash
export SOLANA_RPC_URL="https://mainnet.helius-rpc.com/?api-key=..."
export SOLANA_WALLET_PRIVATE_KEY="<burner-wallet-base58-key>"
```

## Running live 24/7 on your own server

The bot only runs while its backend process is running. To snipe "all the time" you must host it yourself (a small VPS, or your own always-on PC) — it cannot run inside a chat session.

> **Windows users:** see [`WINDOWS_SETUP.md`](WINDOWS_SETUP.md) for a step-by-step guide with one-click `start-bot.bat` / `start-dashboard.bat` launchers and auto-start-on-boot instructions.

Set `SCANNER_AUTOSTART=true` so the scanner arms automatically on boot (no manual click). Copy `backend/.env.example` to `backend/.env` and fill in your values.

1. Copy the project to your server and install (see Quick Start above).
2. Create a git-ignored `backend/.env` (or export the vars) with your real values:
   ```bash
   export SOLANA_RPC_URL="https://mainnet.helius-rpc.com/?api-key=YOUR_KEY"   # a paid/dedicated RPC; the free public RPC gets rate-limited (HTTP 429) under scan load
   export SOLANA_WALLET_PRIVATE_KEY="<burner-wallet-base58-key>"             # dedicated burner, small funds only
   export LIVE_MODE=true
   export AUTO_BUY_ENABLED=true
   export AUTO_SELL_ENABLED=true
   export BUY_AMOUNT_SOL=0.02                                                # keep small; this is your max risk per trade
   ```
3. Start the backend (e.g. with `nohup`, `tmux`, `systemd`, or `pm2`), then start the scanner from the dashboard (or `POST /api/scanner/start`).
4. Confirm it is truly live: `GET /api/wallet` should return `"is_live": true` and your real `sol_balance`.

### What to realistically expect
With safety filters ON, the bot **deliberately skips almost every brand-new token**, because freshly launched meme coins typically have one wallet holding ~100% of supply (the rug/honeypot signature). You will see log lines like:
```
Auto-buy skip XLM: Top holder 100.0% > max 30.0%
```
This is correct, protective behavior — not a malfunction. It means few (or zero) buys fire until a token actually passes your checks. Loosening the filters (e.g. raising `max_top_holder_pct`, disabling `require_renounced_mint`) makes buys fire more often **but dramatically increases the chance of buying a honeypot/rug and losing the funds**. There is no setting that produces guaranteed profit.

> Use a dedicated paid RPC. The free `api.mainnet-beta.solana.com` returns `429 Too Many Requests` under continuous scanning, which can make balances momentarily read as 0 and miss detections.

## Architecture

```
sol-sniper/
├── backend/
│   ├── main.py          # FastAPI app + WebSocket + REST endpoints
│   ├── config.py        # Bot configuration + Solana program IDs
│   ├── models.py        # Pydantic models
│   ├── scanner.py       # Token scanner (Pump.fun, Raydium, Jupiter real feeds)
│   ├── analyzer.py      # Rug-pull detection + risk scoring
│   ├── trader.py        # Auto-trading engine (buy/sell/TP/SL, live + dry-run)
│   ├── solana_client.py # Wallet keypair + RPC connection + balances
│   ├── jupiter.py       # Jupiter swap integration (quote/build/sign/send)
│   ├── market_data.py   # Live prices, decimals, recent-token feed
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
