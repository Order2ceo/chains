"""Solana Meme Coin Sniper Bot — FastAPI Backend."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import BotConfig, load_config
from models import (
    BotStats,
    ConfigUpdate,
    DashboardData,
    Platform,
    Position,
    PositionStatus,
    RiskLevel,
    SecurityAnalysis,
    TokenInfo,
    Trade,
    TradeAction,
    TradeStatus,
)
from scanner import TokenScanner, generate_simulated_positions, generate_simulated_tokens
from trader import TradingEngine
from analyzer import analyze_token, passes_safety_filters
from ws_manager import ConnectionManager
from database import init_db
from solana_client import SolanaClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global state
config = load_config()
sol_client = SolanaClient(config.rpc_url, config.wallet_private_key or None)
scanner = TokenScanner(config)
trader = TradingEngine(config, sol_client)
ws_manager = ConnectionManager()
scanner_task: asyncio.Task | None = None
monitor_task: asyncio.Task | None = None

# Simulated data for demo mode
demo_tokens: list[TokenInfo] = []
demo_positions: list[dict] = []


async def _wallet_balance() -> float:
    """Real SOL balance when a wallet is loaded, else demo value of 10.0."""
    if sol_client.has_wallet:
        try:
            return round(await sol_client.get_sol_balance(), 4)
        except Exception as e:  # noqa: BLE001
            logger.error("wallet balance error: %s", e)
            return 0.0
    return 10.0


async def _price_monitor_loop() -> None:
    """Background loop to update prices and check TP/SL."""
    while True:
        try:
            await trader.update_prices()
            await trader.check_tp_sl()

            # Broadcast position updates
            positions = [p.model_dump(mode="json") for p in trader.get_all_positions()]
            if positions:
                await ws_manager.broadcast("positions_update", positions)
        except Exception as e:
            logger.error(f"Price monitor error: {e}")
        await asyncio.sleep(3)


async def handle_new_token(token: TokenInfo) -> None:
    """Scanner callback: analyze a newly-detected token and auto-buy if it
    passes the configured safety filters and auto-buy is enabled.

    The safety gate lives in `trader.evaluate_token` (auto-buy flag, max
    positions, liquidity, age, security score, and `passes_safety_filters`).
    A real swap only fires when `trader.is_live` (LIVE + wallet loaded);
    otherwise the buy is simulated.
    """
    try:
        await ws_manager.broadcast("new_token", token.model_dump(mode="json"))
    except Exception as e:  # noqa: BLE001
        logger.error("new_token broadcast error: %s", e)

    if not config.auto_buy_enabled:
        return

    try:
        analysis = await analyze_token(token.mint, config)
    except Exception as e:  # noqa: BLE001
        logger.error("auto-buy analysis error for %s: %s", token.mint, e)
        return

    try:
        bought = await trader.evaluate_token(token, analysis)
    except Exception as e:  # noqa: BLE001
        logger.error("auto-buy evaluate error for %s: %s", token.mint, e)
        return

    if bought:
        position = trader.positions.get(token.mint)
        logger.info(
            "AUTO-BUY executed: %s (live=%s)", token.symbol, trader.is_live
        )
        await ws_manager.broadcast(
            "auto_buy",
            {
                "token": token.model_dump(mode="json"),
                "position": position.model_dump(mode="json")
                if position
                else None,
                "live": trader.is_live,
            },
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    global demo_tokens, demo_positions
    await init_db(config.db_path)
    demo_tokens = generate_simulated_tokens(15)
    demo_positions = generate_simulated_positions()
    scanner.on_new_token(handle_new_token)
    logger.info(
        "Solana Sniper Bot backend started (auto_buy=%s, live=%s)",
        config.auto_buy_enabled,
        trader.is_live,
    )
    yield
    if scanner_task and not scanner_task.done():
        scanner_task.cancel()
    if monitor_task and not monitor_task.done():
        monitor_task.cancel()
    await scanner.stop()
    logger.info("Solana Sniper Bot backend stopped")


app = FastAPI(
    title="SOL Meme Coin Sniper Bot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ──────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "scanner_active": scanner.running, "version": "1.0.0"}


@app.get("/api/wallet")
async def get_wallet():
    """Wallet status: connection, address, live SOL balance, and trading mode."""
    connected = sol_client.has_wallet
    balance = 0.0
    if connected:
        try:
            balance = await sol_client.get_sol_balance()
        except Exception as e:  # noqa: BLE001
            logger.error("wallet balance error: %s", e)
    return {
        "connected": connected,
        "address": sol_client.wallet_address,
        "sol_balance": balance,
        "rpc_configured": bool(config.rpc_url),
        "live_mode": config.live_mode,
        "is_live": trader.is_live,
    }


@app.post("/api/live-mode")
async def set_live_mode(payload: dict):
    """Enable/disable live trading. Requires a loaded wallet to go live."""
    enable = bool(payload.get("enabled", False))
    if enable and not sol_client.has_wallet:
        return {
            "status": "error",
            "error": "No wallet configured — set SOLANA_WALLET_PRIVATE_KEY to trade live.",
            "live_mode": config.live_mode,
            "is_live": trader.is_live,
        }
    config.live_mode = enable
    await ws_manager.broadcast(
        "live_mode", {"live_mode": config.live_mode, "is_live": trader.is_live}
    )
    return {
        "status": "ok",
        "live_mode": config.live_mode,
        "is_live": trader.is_live,
    }


@app.get("/api/dashboard")
async def get_dashboard() -> DashboardData:
    """Get complete dashboard data."""
    # Use simulated data for demo, real data when scanner is running
    positions_list: list[Position] = []
    if trader.get_all_positions():
        positions_list = trader.get_all_positions()
    else:
        positions_list = [Position(**p) for p in demo_positions]

    tokens = scanner.get_recent_tokens(20) if scanner.running else demo_tokens
    trades = trader.get_trade_history()

    # Calculate stats
    open_pos = [p for p in positions_list if p.status == PositionStatus.OPEN]
    closed_pos = [p for p in positions_list if p.status != PositionStatus.OPEN]

    winning = sum(1 for p in closed_pos if p.pnl_sol > 0)
    losing = sum(1 for p in closed_pos if p.pnl_sol <= 0)
    total_invested = sum(p.invested_sol for p in closed_pos)
    total_pnl = sum(p.pnl_sol for p in closed_pos)
    total_pnl_open = sum(p.pnl_sol for p in open_pos)

    stats = BotStats(
        total_trades=len(trades) or len(closed_pos),
        winning_trades=winning,
        losing_trades=losing,
        win_rate=round(winning / len(closed_pos) * 100, 1) if closed_pos else 0,
        total_invested_sol=round(total_invested, 4),
        total_returned_sol=round(total_invested + total_pnl, 4),
        total_pnl_sol=round(total_pnl + total_pnl_open, 4),
        total_pnl_pct=round(
            (total_pnl / total_invested * 100) if total_invested > 0 else 0, 1
        ),
        best_trade_pnl_pct=round(
            max((p.pnl_pct for p in closed_pos), default=0), 1
        ),
        worst_trade_pnl_pct=round(
            min((p.pnl_pct for p in closed_pos), default=0), 1
        ),
        open_positions=len(open_pos),
        sol_balance=await _wallet_balance(),
        wallet_address=sol_client.wallet_address or "Demo...Wallet",
    )

    return DashboardData(
        stats=stats,
        positions=positions_list,
        recent_tokens=tokens,
        recent_trades=trades,
        scanner_active=scanner.running,
        auto_buy_enabled=config.auto_buy_enabled,
        auto_sell_enabled=config.auto_sell_enabled,
    )


@app.get("/api/tokens")
async def get_tokens(limit: int = 20) -> list[TokenInfo]:
    """Get recently detected tokens."""
    if scanner.running:
        return scanner.get_recent_tokens(limit)
    return demo_tokens[:limit]


@app.get("/api/tokens/{mint}/analysis")
async def get_token_analysis(mint: str) -> SecurityAnalysis:
    """Get security analysis for a specific token."""
    return await analyze_token(mint, config)


@app.get("/api/positions")
async def get_positions() -> list[Position]:
    """Get all positions."""
    if trader.get_all_positions():
        return trader.get_all_positions()
    return [Position(**p) for p in demo_positions]


@app.get("/api/trades")
async def get_trades(limit: int = 50) -> list[Trade]:
    """Get trade history."""
    return trader.get_trade_history()[:limit]


@app.post("/api/buy/{mint}")
async def manual_buy(mint: str):
    """Manually trigger a buy for a token."""
    # Find token info from the current scan/demo feed first.
    token = None
    for t in demo_tokens:
        if t.mint == mint:
            token = t
            break

    # In live mode, look up real on-chain market data for arbitrary mints.
    if token is None and trader.is_live:
        import aiohttp
        import market_data

        async with aiohttp.ClientSession() as s:
            price_sol, info = await market_data.get_token_price_sol(mint, s)
        if info:
            token = TokenInfo(
                mint=mint,
                symbol=info["symbol"],
                name=info["name"],
                platform=Platform.JUPITER,
                current_price_sol=price_sol or 0.0000001,
                current_price_usd=info["price_usd"],
                initial_liquidity_sol=0.0,
            )

    if not token:
        token = TokenInfo(
            mint=mint,
            symbol="???",
            platform=Platform.RAYDIUM,
            current_price_sol=0.0000001,
        )

    trade = await trader.execute_buy(token)
    if trade:
        await ws_manager.broadcast("trade_executed", trade.model_dump(mode="json"))
        return {"status": "success", "trade": trade.model_dump(mode="json")}
    return {"status": "failed", "error": "Trade execution failed"}


@app.post("/api/sell/{mint}")
async def manual_sell(mint: str):
    """Manually trigger a sell for a position."""
    trade = await trader.execute_sell(mint, reason="manual")
    if trade:
        await ws_manager.broadcast("trade_executed", trade.model_dump(mode="json"))
        return {"status": "success", "trade": trade.model_dump(mode="json")}
    return {"status": "failed", "error": "No open position or sell failed"}


@app.get("/api/config")
async def get_config():
    """Get current bot configuration."""
    return {
        "buy_amount_sol": config.buy_amount_sol,
        "max_buy_amount_sol": config.max_buy_amount_sol,
        "take_profit_pct": config.take_profit_pct,
        "stop_loss_pct": config.stop_loss_pct,
        "trailing_stop_pct": config.trailing_stop_pct,
        "slippage_bps": config.slippage_bps,
        "min_liquidity_sol": config.min_liquidity_sol,
        "max_token_age_seconds": config.max_token_age_seconds,
        "max_top_holder_pct": config.max_top_holder_pct,
        "auto_buy_enabled": config.auto_buy_enabled,
        "auto_sell_enabled": config.auto_sell_enabled,
        "max_concurrent_positions": config.max_concurrent_positions,
        "require_locked_liquidity": config.require_locked_liquidity,
        "require_renounced_mint": config.require_renounced_mint,
        "require_no_freeze": config.require_no_freeze,
        "platforms": config.platforms,
        "scanner_active": scanner.running,
    }


@app.post("/api/config")
async def update_config(update: ConfigUpdate):
    """Update bot configuration."""
    if update.buy_amount_sol is not None:
        config.buy_amount_sol = update.buy_amount_sol
    if update.take_profit_pct is not None:
        config.take_profit_pct = update.take_profit_pct
    if update.stop_loss_pct is not None:
        config.stop_loss_pct = update.stop_loss_pct
    if update.trailing_stop_pct is not None:
        config.trailing_stop_pct = update.trailing_stop_pct
    if update.slippage_bps is not None:
        config.slippage_bps = update.slippage_bps
    if update.min_liquidity_sol is not None:
        config.min_liquidity_sol = update.min_liquidity_sol
    if update.max_token_age_seconds is not None:
        config.max_token_age_seconds = update.max_token_age_seconds
    if update.max_top_holder_pct is not None:
        config.max_top_holder_pct = update.max_top_holder_pct
    if update.auto_buy_enabled is not None:
        config.auto_buy_enabled = update.auto_buy_enabled
    if update.auto_sell_enabled is not None:
        config.auto_sell_enabled = update.auto_sell_enabled
    if update.max_concurrent_positions is not None:
        config.max_concurrent_positions = update.max_concurrent_positions
    if update.require_locked_liquidity is not None:
        config.require_locked_liquidity = update.require_locked_liquidity
    if update.require_renounced_mint is not None:
        config.require_renounced_mint = update.require_renounced_mint
    if update.require_no_freeze is not None:
        config.require_no_freeze = update.require_no_freeze
    if update.platforms is not None:
        config.platforms = update.platforms

    await ws_manager.broadcast("config_update", {"config": await get_config()})
    return {"status": "updated"}


@app.post("/api/scanner/start")
async def start_scanner():
    """Start the token scanner."""
    global scanner_task, monitor_task
    if scanner.running:
        return {"status": "already_running"}

    scanner_task = asyncio.create_task(scanner.start())
    monitor_task = asyncio.create_task(_price_monitor_loop())
    await ws_manager.broadcast("scanner_status", {"active": True})
    return {"status": "started"}


@app.post("/api/scanner/stop")
async def stop_scanner():
    """Stop the token scanner."""
    global scanner_task, monitor_task
    await scanner.stop()
    if scanner_task and not scanner_task.done():
        scanner_task.cancel()
    if monitor_task and not monitor_task.done():
        monitor_task.cancel()
    await ws_manager.broadcast("scanner_status", {"active": False})
    return {"status": "stopped"}


# ── WebSocket ───────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    try:
        # Send initial data
        dashboard = await get_dashboard()
        await ws_manager.send_personal(
            websocket, "initial_data", dashboard.model_dump(mode="json")
        )

        while True:
            data = await websocket.receive_text()
            logger.debug(f"WS received: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
