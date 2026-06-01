"""Pydantic models for the Solana Sniper Bot."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Platform(str, Enum):
    PUMPFUN = "pumpfun"
    RAYDIUM = "raydium"
    JUPITER = "jupiter"
    ORCA = "orca"


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SCAM = "scam"


class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    STOPPED_OUT = "stopped_out"
    TAKE_PROFIT = "take_profit"


class TokenInfo(BaseModel):
    """Detected token information."""

    mint: str
    name: str = "Unknown"
    symbol: str = "???"
    decimals: int = 9
    platform: Platform
    pool_address: str = ""
    base_mint: str = ""
    quote_mint: str = ""
    initial_liquidity_sol: float = 0.0
    current_price_sol: float = 0.0
    current_price_usd: float = 0.0
    market_cap_usd: float = 0.0
    volume_24h_usd: float = 0.0
    holder_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class SecurityAnalysis(BaseModel):
    """Token security analysis results."""

    mint: str
    risk_level: RiskLevel = RiskLevel.HIGH
    score: int = 0  # 0-100, higher is safer

    # Checks
    mint_authority_revoked: bool = False
    freeze_authority_revoked: bool = False
    liquidity_locked: bool = False
    liquidity_lock_duration_days: int = 0
    top_holder_pct: float = 100.0
    top_10_holder_pct: float = 100.0
    has_honeypot_risk: bool = True
    is_mintable: bool = True
    supply_concentration: float = 100.0
    lp_burned_pct: float = 0.0

    # Metadata
    has_social_links: bool = False
    has_website: bool = False
    warnings: list[str] = Field(default_factory=list)
    passed_checks: list[str] = Field(default_factory=list)


class Trade(BaseModel):
    """Individual trade record."""

    id: str = ""
    token_mint: str
    token_symbol: str = "???"
    action: TradeAction
    amount_sol: float
    amount_tokens: float = 0.0
    price_sol: float = 0.0
    price_usd: float = 0.0
    tx_signature: str = ""
    status: TradeStatus = TradeStatus.PENDING
    platform: Platform = Platform.RAYDIUM
    slippage_bps: int = 500
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Position(BaseModel):
    """Active or closed position."""

    id: str = ""
    token_mint: str
    token_symbol: str = "???"
    token_name: str = "Unknown"
    platform: Platform = Platform.RAYDIUM
    entry_price_sol: float = 0.0
    entry_price_usd: float = 0.0
    current_price_sol: float = 0.0
    current_price_usd: float = 0.0
    amount_tokens: float = 0.0
    invested_sol: float = 0.0
    current_value_sol: float = 0.0
    pnl_sol: float = 0.0
    pnl_pct: float = 0.0
    highest_price_sol: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    buy_tx: str = ""
    sell_tx: str = ""
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: datetime | None = None
    risk_level: RiskLevel = RiskLevel.HIGH


class BotStats(BaseModel):
    """Overall bot statistics."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_invested_sol: float = 0.0
    total_returned_sol: float = 0.0
    total_pnl_sol: float = 0.0
    total_pnl_pct: float = 0.0
    best_trade_pnl_pct: float = 0.0
    worst_trade_pnl_pct: float = 0.0
    open_positions: int = 0
    sol_balance: float = 0.0
    wallet_address: str = ""


class DashboardData(BaseModel):
    """Complete dashboard data."""

    stats: BotStats
    positions: list[Position] = Field(default_factory=list)
    recent_tokens: list[TokenInfo] = Field(default_factory=list)
    recent_trades: list[Trade] = Field(default_factory=list)
    scanner_active: bool = False
    auto_buy_enabled: bool = False
    auto_sell_enabled: bool = True


class ConfigUpdate(BaseModel):
    """Configuration update request."""

    buy_amount_sol: float | None = None
    take_profit_pct: float | None = None
    stop_loss_pct: float | None = None
    trailing_stop_pct: float | None = None
    slippage_bps: int | None = None
    min_liquidity_sol: float | None = None
    max_token_age_seconds: int | None = None
    max_top_holder_pct: float | None = None
    auto_buy_enabled: bool | None = None
    auto_sell_enabled: bool | None = None
    max_concurrent_positions: int | None = None
    require_locked_liquidity: bool | None = None
    require_renounced_mint: bool | None = None
    require_no_freeze: bool | None = None
    platforms: list[str] | None = None


class SniperEvent(BaseModel):
    """WebSocket event for real-time updates."""

    event: str  # new_token, trade_executed, position_update, price_update, alert
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
