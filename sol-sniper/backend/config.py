"""Configuration for the Solana Sniper Bot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class BotConfig:
    """Bot trading configuration."""

    # RPC endpoints
    rpc_url: str = "https://api.mainnet-beta.solana.com"
    ws_url: str = "wss://api.mainnet-beta.solana.com"

    # Trading parameters
    buy_amount_sol: float = 0.1
    max_buy_amount_sol: float = 1.0
    slippage_bps: int = 500  # 5%
    priority_fee_lamports: int = 100_000

    # Take-profit / Stop-loss
    take_profit_pct: float = 100.0  # 100% gain
    stop_loss_pct: float = 30.0  # 30% loss
    trailing_stop_pct: float = 20.0  # 20% trailing stop

    # Safety filters
    min_liquidity_sol: float = 5.0
    max_token_age_seconds: int = 300  # 5 minutes
    min_holders: int = 10
    max_top_holder_pct: float = 30.0  # Max single holder %
    require_locked_liquidity: bool = True
    require_renounced_mint: bool = True
    require_no_freeze: bool = True

    # Scanner settings
    scan_interval_ms: int = 1000
    platforms: list[str] = field(
        default_factory=lambda: ["pumpfun", "raydium", "jupiter"]
    )

    # Auto-trading
    auto_buy_enabled: bool = False
    auto_sell_enabled: bool = True
    max_concurrent_positions: int = 5

    # Database
    db_path: str = "sniper.db"


# Program IDs
RAYDIUM_AMM_V4 = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_CPMM = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"
JUPITER_V6 = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
PUMPFUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
WSOL_MINT = "So11111111111111111111111111111111111111112"


def load_config() -> BotConfig:
    """Load configuration from environment variables."""
    config = BotConfig()
    config.rpc_url = os.getenv("SOLANA_RPC_URL", config.rpc_url)
    config.ws_url = os.getenv("SOLANA_WS_URL", config.ws_url)
    config.buy_amount_sol = float(
        os.getenv("BUY_AMOUNT_SOL", str(config.buy_amount_sol))
    )
    config.take_profit_pct = float(
        os.getenv("TAKE_PROFIT_PCT", str(config.take_profit_pct))
    )
    config.stop_loss_pct = float(
        os.getenv("STOP_LOSS_PCT", str(config.stop_loss_pct))
    )
    config.auto_buy_enabled = (
        os.getenv("AUTO_BUY_ENABLED", "false").lower() == "true"
    )
    config.auto_sell_enabled = (
        os.getenv("AUTO_SELL_ENABLED", "true").lower() == "true"
    )
    config.db_path = os.getenv("DB_PATH", config.db_path)
    return config
