"""Auto-trading engine — buy/sell execution with TP/SL management."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import aiohttp

import jupiter
import market_data
from analyzer import passes_safety_filters
from config import BotConfig, WSOL_MINT
from models import (
    Platform,
    Position,
    PositionStatus,
    SecurityAnalysis,
    TokenInfo,
    Trade,
    TradeAction,
    TradeStatus,
)
from solana_client import SolanaClient

logger = logging.getLogger(__name__)


class TradingEngine:
    """Handles auto-buy, auto-sell, take-profit, and stop-loss."""

    def __init__(self, config: BotConfig, sol: SolanaClient | None = None):
        self.config = config
        self.sol = sol
        self.positions: dict[str, Position] = {}
        self.trade_history: list[Trade] = []
        self._running = False
        self._callbacks: list[Any] = []
        self._price_cache: dict[str, float] = {}
        self._session: aiohttp.ClientSession | None = None
        # token mint -> decimals, for sizing real sell orders
        self._decimals: dict[str, int] = {}

    @property
    def is_live(self) -> bool:
        """True only when live trading is enabled AND a wallet is loaded."""
        return bool(
            self.config.live_mode and self.sol is not None and self.sol.has_wallet
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def on_trade(self, callback: Any) -> None:
        """Register callback for trade events."""
        self._callbacks.append(callback)

    async def _notify(self, event: str, data: dict) -> None:
        """Notify callbacks of trade events."""
        for cb in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event, data)
                else:
                    cb(event, data)
            except Exception as e:
                logger.error(f"Trade callback error: {e}")

    async def evaluate_token(
        self,
        token: TokenInfo,
        analysis: SecurityAnalysis,
    ) -> bool:
        """Evaluate whether to buy a newly detected token."""
        if not self.config.auto_buy_enabled:
            logger.debug(f"Auto-buy disabled, skipping {token.symbol}")
            return False

        if len(self.positions) >= self.config.max_concurrent_positions:
            logger.info("Max concurrent positions reached")
            return False

        if token.mint in self.positions:
            logger.debug(f"Already have position in {token.symbol}")
            return False

        # Check liquidity
        if token.initial_liquidity_sol < self.config.min_liquidity_sol:
            logger.info(
                f"Insufficient liquidity for {token.symbol}: "
                f"{token.initial_liquidity_sol} SOL < {self.config.min_liquidity_sol} SOL"
            )
            return False

        # Check token age
        age_seconds = (datetime.utcnow() - token.created_at).total_seconds()
        if age_seconds > self.config.max_token_age_seconds:
            logger.info(
                f"Token {token.symbol} too old: {age_seconds:.0f}s > {self.config.max_token_age_seconds}s"
            )
            return False

        # Check security analysis score
        if analysis.score < 40:
            logger.info(
                f"Token {token.symbol} failed security check: score {analysis.score}/100"
            )
            return False

        # Apply the user-configured rug-pull / safety filters
        passed, failures = passes_safety_filters(analysis, self.config)
        if not passed:
            logger.info(
                "Auto-buy skip %s: %s", token.symbol, "; ".join(failures)
            )
            return False

        # Execute buy
        logger.info(
            "Auto-buy: %s passed all filters (score %s) — buying",
            token.symbol,
            analysis.score,
        )
        trade = await self.execute_buy(token)
        return trade is not None

    async def execute_buy(self, token: TokenInfo) -> Trade | None:
        """Execute a buy trade for a token."""
        trade_id = str(uuid.uuid4())[:8]
        amount_sol = min(self.config.buy_amount_sol, self.config.max_buy_amount_sol)

        trade = Trade(
            id=trade_id,
            token_mint=token.mint,
            token_symbol=token.symbol,
            action=TradeAction.BUY,
            amount_sol=amount_sol,
            price_sol=token.current_price_sol,
            price_usd=token.current_price_usd,
            platform=token.platform,
            slippage_bps=self.config.slippage_bps,
            status=TradeStatus.PENDING,
        )

        logger.info(
            f"Executing BUY: {token.symbol} | {amount_sol} SOL | "
            f"Price: {token.current_price_sol:.10f} SOL"
        )

        try:
            tx_sig: str | None
            tokens_received = 0.0
            if self.is_live:
                session = await self._get_session()
                result = await jupiter.buy_token(
                    token.mint,
                    amount_sol,
                    self.config.slippage_bps,
                    self.sol,
                    session,
                    self.config.priority_fee_lamports,
                )
                if not result.ok:
                    logger.error("Live BUY failed for %s: %s", token.symbol, result.error)
                    trade.status = TradeStatus.FAILED
                    self.trade_history.append(trade)
                    return None
                tx_sig = result.tx_signature
                tokens_received = result.out_amount
            else:
                tx_sig = await self._simulate_swap(
                    token.mint, amount_sol, TradeAction.BUY, token.platform
                )

            if tx_sig:
                trade.tx_signature = tx_sig
                trade.status = TradeStatus.CONFIRMED
                trade.amount_tokens = tokens_received or (
                    amount_sol / token.current_price_sol
                    if token.current_price_sol > 0
                    else 0
                )

                # Create position
                position = Position(
                    id=f"pos-{trade_id}",
                    token_mint=token.mint,
                    token_symbol=token.symbol,
                    token_name=token.name,
                    platform=token.platform,
                    entry_price_sol=token.current_price_sol,
                    entry_price_usd=token.current_price_usd,
                    current_price_sol=token.current_price_sol,
                    current_price_usd=token.current_price_usd,
                    amount_tokens=trade.amount_tokens,
                    invested_sol=amount_sol,
                    current_value_sol=amount_sol,
                    pnl_sol=0,
                    pnl_pct=0,
                    highest_price_sol=token.current_price_sol,
                    status=PositionStatus.OPEN,
                    buy_tx=tx_sig,
                )
                self.positions[token.mint] = position

                self.trade_history.append(trade)
                await self._notify(
                    "trade_executed",
                    {"trade": trade.model_dump(), "position": position.model_dump()},
                )
                logger.info(f"BUY confirmed: {token.symbol} | TX: {tx_sig[:16]}...")
                return trade
            else:
                trade.status = TradeStatus.FAILED
                logger.error(f"BUY failed: {token.symbol}")

        except Exception as e:
            trade.status = TradeStatus.FAILED
            logger.error(f"BUY error for {token.symbol}: {e}")

        self.trade_history.append(trade)
        return None

    async def execute_sell(self, mint: str, reason: str = "manual") -> Trade | None:
        """Execute a sell trade for a position."""
        position = self.positions.get(mint)
        if not position or position.status != PositionStatus.OPEN:
            logger.warning(f"No open position for {mint}")
            return None

        trade_id = str(uuid.uuid4())[:8]
        trade = Trade(
            id=trade_id,
            token_mint=mint,
            token_symbol=position.token_symbol,
            action=TradeAction.SELL,
            amount_sol=position.current_value_sol,
            amount_tokens=position.amount_tokens,
            price_sol=position.current_price_sol,
            price_usd=position.current_price_usd,
            platform=position.platform,
            slippage_bps=self.config.slippage_bps,
            status=TradeStatus.PENDING,
        )

        logger.info(
            f"Executing SELL: {position.token_symbol} | Reason: {reason} | "
            f"PnL: {position.pnl_pct:+.1f}%"
        )

        try:
            tx_sig: str | None
            if self.is_live:
                session = await self._get_session()
                decimals = await jupiter._get_decimals(mint, session)
                # Sell the actual on-chain balance to avoid dust/rounding leftovers.
                ui_balance = await self.sol.get_token_balance(mint)
                amount_to_sell = ui_balance or position.amount_tokens
                base_units = int(amount_to_sell * (10**decimals))
                if base_units <= 0:
                    logger.error("Live SELL: zero token balance for %s", mint)
                    trade.status = TradeStatus.FAILED
                    self.trade_history.append(trade)
                    return None
                result = await jupiter.sell_token(
                    mint,
                    base_units,
                    self.config.slippage_bps,
                    self.sol,
                    session,
                    self.config.priority_fee_lamports,
                )
                if not result.ok:
                    logger.error(
                        "Live SELL failed for %s: %s",
                        position.token_symbol,
                        result.error,
                    )
                    trade.status = TradeStatus.FAILED
                    self.trade_history.append(trade)
                    return None
                tx_sig = result.tx_signature
                trade.amount_sol = result.out_amount
            else:
                tx_sig = await self._simulate_swap(
                    mint, position.amount_tokens, TradeAction.SELL, position.platform
                )

            if tx_sig:
                trade.tx_signature = tx_sig
                trade.status = TradeStatus.CONFIRMED

                if reason == "take_profit":
                    position.status = PositionStatus.TAKE_PROFIT
                elif reason == "stop_loss" or reason == "trailing_stop":
                    position.status = PositionStatus.STOPPED_OUT
                else:
                    position.status = PositionStatus.CLOSED

                position.sell_tx = tx_sig
                position.closed_at = datetime.utcnow()

                self.trade_history.append(trade)
                await self._notify(
                    "trade_executed",
                    {"trade": trade.model_dump(), "position": position.model_dump()},
                )
                logger.info(
                    f"SELL confirmed: {position.token_symbol} | "
                    f"PnL: {position.pnl_pct:+.1f}% | TX: {tx_sig[:16]}..."
                )
                return trade
            else:
                trade.status = TradeStatus.FAILED

        except Exception as e:
            trade.status = TradeStatus.FAILED
            logger.error(f"SELL error for {position.token_symbol}: {e}")

        self.trade_history.append(trade)
        return None

    async def check_tp_sl(self) -> None:
        """Check take-profit and stop-loss for all open positions."""
        if not self.config.auto_sell_enabled:
            return

        for mint, position in list(self.positions.items()):
            if position.status != PositionStatus.OPEN:
                continue

            # Take-profit
            if position.pnl_pct >= self.config.take_profit_pct:
                logger.info(
                    f"Take-profit triggered for {position.token_symbol}: "
                    f"{position.pnl_pct:+.1f}% >= {self.config.take_profit_pct}%"
                )
                await self.execute_sell(mint, reason="take_profit")
                continue

            # Stop-loss
            if position.pnl_pct <= -self.config.stop_loss_pct:
                logger.info(
                    f"Stop-loss triggered for {position.token_symbol}: "
                    f"{position.pnl_pct:+.1f}% <= -{self.config.stop_loss_pct}%"
                )
                await self.execute_sell(mint, reason="stop_loss")
                continue

            # Trailing stop
            if position.highest_price_sol > 0 and position.current_price_sol > 0:
                drop_from_high = (
                    (position.highest_price_sol - position.current_price_sol)
                    / position.highest_price_sol
                    * 100
                )
                if (
                    drop_from_high >= self.config.trailing_stop_pct
                    and position.pnl_pct > 0
                ):
                    logger.info(
                        f"Trailing stop triggered for {position.token_symbol}: "
                        f"{drop_from_high:.1f}% drop from high"
                    )
                    await self.execute_sell(mint, reason="trailing_stop")

    async def update_prices(self) -> None:
        """Update current prices for all open positions.

        Uses real on-chain prices in live mode, otherwise simulates movement.
        """
        import random

        session = await self._get_session() if self.is_live else None
        sol_usd = (
            await market_data.get_sol_price_usd(session) if session else 170.0
        )

        for mint, position in self.positions.items():
            if position.status != PositionStatus.OPEN:
                continue

            if self.is_live and session is not None:
                price_sol, info = await market_data.get_token_price_sol(mint, session)
                if price_sol <= 0:
                    continue
                new_price = price_sol
                position.current_price_sol = new_price
                position.current_price_usd = (
                    info["price_usd"] if info else new_price * sol_usd
                )
            else:
                # Simulate price movement
                change = random.uniform(-0.05, 0.08)
                new_price = position.current_price_sol * (1 + change)
                position.current_price_sol = new_price
                position.current_price_usd = new_price * 170

            # Update PnL
            position.current_value_sol = new_price * position.amount_tokens
            position.pnl_sol = position.current_value_sol - position.invested_sol
            position.pnl_pct = (
                (position.pnl_sol / position.invested_sol * 100)
                if position.invested_sol > 0
                else 0
            )

            # Track highest price
            if new_price > position.highest_price_sol:
                position.highest_price_sol = new_price

    async def _simulate_swap(
        self,
        mint: str,
        amount: float,
        action: TradeAction,
        platform: Platform,
    ) -> str:
        """Simulate a swap transaction. Returns a fake tx signature."""
        await asyncio.sleep(0.1)  # Simulate network delay
        import hashlib

        data = f"{mint}{amount}{action.value}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:88]

    def get_open_positions(self) -> list[Position]:
        """Get all open positions."""
        return [p for p in self.positions.values() if p.status == PositionStatus.OPEN]

    def get_all_positions(self) -> list[Position]:
        """Get all positions."""
        return list(self.positions.values())

    def get_trade_history(self) -> list[Trade]:
        """Get trade history."""
        return sorted(self.trade_history, key=lambda t: t.timestamp, reverse=True)
