"""SQLite database for trade history and positions."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

import aiosqlite

from models import (
    BotStats,
    Platform,
    Position,
    PositionStatus,
    Trade,
    TradeAction,
    TradeStatus,
)

DB_PATH = "sniper.db"


async def init_db(path: str = DB_PATH) -> None:
    """Initialize the database schema."""
    global DB_PATH
    DB_PATH = path
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                token_mint TEXT NOT NULL,
                token_symbol TEXT DEFAULT '???',
                action TEXT NOT NULL,
                amount_sol REAL NOT NULL,
                amount_tokens REAL DEFAULT 0,
                price_sol REAL DEFAULT 0,
                price_usd REAL DEFAULT 0,
                tx_signature TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                platform TEXT DEFAULT 'raydium',
                slippage_bps INTEGER DEFAULT 500,
                timestamp TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                token_mint TEXT NOT NULL,
                token_symbol TEXT DEFAULT '???',
                token_name TEXT DEFAULT 'Unknown',
                platform TEXT DEFAULT 'raydium',
                entry_price_sol REAL DEFAULT 0,
                entry_price_usd REAL DEFAULT 0,
                current_price_sol REAL DEFAULT 0,
                current_price_usd REAL DEFAULT 0,
                amount_tokens REAL DEFAULT 0,
                invested_sol REAL DEFAULT 0,
                current_value_sol REAL DEFAULT 0,
                pnl_sol REAL DEFAULT 0,
                pnl_pct REAL DEFAULT 0,
                highest_price_sol REAL DEFAULT 0,
                status TEXT DEFAULT 'open',
                buy_tx TEXT DEFAULT '',
                sell_tx TEXT DEFAULT '',
                risk_level TEXT DEFAULT 'high',
                opened_at TEXT NOT NULL,
                closed_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS detected_tokens (
                mint TEXT PRIMARY KEY,
                name TEXT DEFAULT 'Unknown',
                symbol TEXT DEFAULT '???',
                platform TEXT,
                pool_address TEXT DEFAULT '',
                initial_liquidity_sol REAL DEFAULT 0,
                current_price_sol REAL DEFAULT 0,
                market_cap_usd REAL DEFAULT 0,
                holder_count INTEGER DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'high',
                security_data TEXT DEFAULT '{}',
                detected_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def save_trade(trade: Trade) -> Trade:
    """Save a trade to the database."""
    if not trade.id:
        trade.id = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO trades 
               (id, token_mint, token_symbol, action, amount_sol, amount_tokens,
                price_sol, price_usd, tx_signature, status, platform, slippage_bps, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trade.id,
                trade.token_mint,
                trade.token_symbol,
                trade.action.value,
                trade.amount_sol,
                trade.amount_tokens,
                trade.price_sol,
                trade.price_usd,
                trade.tx_signature,
                trade.status.value,
                trade.platform.value,
                trade.slippage_bps,
                trade.timestamp.isoformat(),
            ),
        )
        await db.commit()
    return trade


async def save_position(position: Position) -> Position:
    """Save or update a position."""
    if not position.id:
        position.id = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO positions
               (id, token_mint, token_symbol, token_name, platform,
                entry_price_sol, entry_price_usd, current_price_sol, current_price_usd,
                amount_tokens, invested_sol, current_value_sol, pnl_sol, pnl_pct,
                highest_price_sol, status, buy_tx, sell_tx, risk_level, opened_at, closed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                position.id,
                position.token_mint,
                position.token_symbol,
                position.token_name,
                position.platform.value,
                position.entry_price_sol,
                position.entry_price_usd,
                position.current_price_sol,
                position.current_price_usd,
                position.amount_tokens,
                position.invested_sol,
                position.current_value_sol,
                position.pnl_sol,
                position.pnl_pct,
                position.highest_price_sol,
                position.status.value,
                position.buy_tx,
                position.sell_tx,
                position.risk_level.value,
                position.opened_at.isoformat(),
                position.closed_at.isoformat() if position.closed_at else None,
            ),
        )
        await db.commit()
    return position


async def get_open_positions() -> list[Position]:
    """Get all open positions."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM positions WHERE status = 'open' ORDER BY opened_at DESC"
        )
        rows = await cursor.fetchall()
        return [
            Position(
                id=row["id"],
                token_mint=row["token_mint"],
                token_symbol=row["token_symbol"],
                token_name=row["token_name"],
                platform=Platform(row["platform"]),
                entry_price_sol=row["entry_price_sol"],
                entry_price_usd=row["entry_price_usd"],
                current_price_sol=row["current_price_sol"],
                current_price_usd=row["current_price_usd"],
                amount_tokens=row["amount_tokens"],
                invested_sol=row["invested_sol"],
                current_value_sol=row["current_value_sol"],
                pnl_sol=row["pnl_sol"],
                pnl_pct=row["pnl_pct"],
                highest_price_sol=row["highest_price_sol"],
                status=PositionStatus(row["status"]),
                buy_tx=row["buy_tx"],
                sell_tx=row["sell_tx"],
                risk_level=row["risk_level"],
                opened_at=datetime.fromisoformat(row["opened_at"]),
                closed_at=(
                    datetime.fromisoformat(row["closed_at"])
                    if row["closed_at"]
                    else None
                ),
            )
            for row in rows
        ]


async def get_all_positions(limit: int = 50) -> list[Position]:
    """Get all positions (open and closed)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM positions ORDER BY opened_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            Position(
                id=row["id"],
                token_mint=row["token_mint"],
                token_symbol=row["token_symbol"],
                token_name=row["token_name"],
                platform=Platform(row["platform"]),
                entry_price_sol=row["entry_price_sol"],
                entry_price_usd=row["entry_price_usd"],
                current_price_sol=row["current_price_sol"],
                current_price_usd=row["current_price_usd"],
                amount_tokens=row["amount_tokens"],
                invested_sol=row["invested_sol"],
                current_value_sol=row["current_value_sol"],
                pnl_sol=row["pnl_sol"],
                pnl_pct=row["pnl_pct"],
                highest_price_sol=row["highest_price_sol"],
                status=PositionStatus(row["status"]),
                buy_tx=row["buy_tx"],
                sell_tx=row["sell_tx"],
                risk_level=row["risk_level"],
                opened_at=datetime.fromisoformat(row["opened_at"]),
                closed_at=(
                    datetime.fromisoformat(row["closed_at"])
                    if row["closed_at"]
                    else None
                ),
            )
            for row in rows
        ]


async def get_recent_trades(limit: int = 50) -> list[Trade]:
    """Get recent trades."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [
            Trade(
                id=row["id"],
                token_mint=row["token_mint"],
                token_symbol=row["token_symbol"],
                action=TradeAction(row["action"]),
                amount_sol=row["amount_sol"],
                amount_tokens=row["amount_tokens"],
                price_sol=row["price_sol"],
                price_usd=row["price_usd"],
                tx_signature=row["tx_signature"],
                status=TradeStatus(row["status"]),
                platform=Platform(row["platform"]),
                slippage_bps=row["slippage_bps"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]


async def get_bot_stats() -> BotStats:
    """Calculate overall bot statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Total trades
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM trades WHERE status = 'confirmed'"
        )
        row = await cursor.fetchone()
        total_trades = row["cnt"] if row else 0

        # Closed positions stats
        cursor = await db.execute(
            "SELECT * FROM positions WHERE status != 'open'"
        )
        closed = await cursor.fetchall()

        winning = sum(1 for p in closed if p["pnl_sol"] > 0)
        losing = sum(1 for p in closed if p["pnl_sol"] <= 0)
        total_invested = sum(p["invested_sol"] for p in closed)
        total_returned = sum(
            p["invested_sol"] + p["pnl_sol"] for p in closed
        )
        total_pnl = sum(p["pnl_sol"] for p in closed)

        best_pnl = max((p["pnl_pct"] for p in closed), default=0.0)
        worst_pnl = min((p["pnl_pct"] for p in closed), default=0.0)

        # Open positions
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM positions WHERE status = 'open'"
        )
        row = await cursor.fetchone()
        open_count = row["cnt"] if row else 0

        win_rate = (winning / len(closed) * 100) if closed else 0.0
        pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

        return BotStats(
            total_trades=total_trades,
            winning_trades=winning,
            losing_trades=losing,
            win_rate=win_rate,
            total_invested_sol=total_invested,
            total_returned_sol=total_returned,
            total_pnl_sol=total_pnl,
            total_pnl_pct=pnl_pct,
            best_trade_pnl_pct=best_pnl,
            worst_trade_pnl_pct=worst_pnl,
            open_positions=open_count,
        )
