"""Token scanner — detects new token launches on Pump.fun, Raydium, Jupiter."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from config import (
    PUMPFUN_PROGRAM,
    RAYDIUM_AMM_V4,
    RAYDIUM_CPMM,
    WSOL_MINT,
    BotConfig,
)
from models import Platform, TokenInfo

logger = logging.getLogger(__name__)


class TokenScanner:
    """Scans for new token launches across platforms."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.detected_tokens: dict[str, TokenInfo] = {}
        self.running = False
        self._callbacks: list[Any] = []
        self._session: aiohttp.ClientSession | None = None
        self._ws: Any = None

    def on_new_token(self, callback: Any) -> None:
        """Register callback for new token detection."""
        self._callbacks.append(callback)

    async def _notify(self, token: TokenInfo) -> None:
        """Notify all registered callbacks."""
        for cb in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(token)
                else:
                    cb(token)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def start(self) -> None:
        """Start scanning for new tokens."""
        self.running = True
        self._session = aiohttp.ClientSession()
        logger.info("Token scanner started")

        tasks = []
        if "pumpfun" in self.config.platforms:
            tasks.append(asyncio.create_task(self._scan_pumpfun()))
        if "raydium" in self.config.platforms:
            tasks.append(asyncio.create_task(self._scan_raydium()))
        if "jupiter" in self.config.platforms:
            tasks.append(asyncio.create_task(self._scan_jupiter()))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self) -> None:
        """Stop the scanner."""
        self.running = False
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        logger.info("Token scanner stopped")

    async def _scan_pumpfun(self) -> None:
        """Monitor Pump.fun for new token launches via log subscription."""
        logger.info("Scanning Pump.fun for new launches...")
        while self.running:
            try:
                await self._poll_pumpfun_api()
            except Exception as e:
                logger.error(f"Pump.fun scan error: {e}")
            await asyncio.sleep(self.config.scan_interval_ms / 1000)

    async def _poll_pumpfun_api(self) -> None:
        """Poll Pump.fun API for new coins."""
        if not self._session:
            return
        try:
            url = "https://frontend-api.pump.fun/coins/latest"
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    coins = data if isinstance(data, list) else [data]
                    for coin in coins[:5]:
                        mint = coin.get("mint", "")
                        if mint and mint not in self.detected_tokens:
                            token = TokenInfo(
                                mint=mint,
                                name=coin.get("name", "Unknown"),
                                symbol=coin.get("symbol", "???"),
                                platform=Platform.PUMPFUN,
                                initial_liquidity_sol=coin.get(
                                    "virtual_sol_reserves", 0
                                )
                                / 1e9,
                                market_cap_usd=coin.get("usd_market_cap", 0),
                                created_at=datetime.utcnow(),
                                detected_at=datetime.utcnow(),
                            )
                            self.detected_tokens[mint] = token
                            logger.info(
                                f"[PUMP.FUN] New token: {token.symbol} ({mint[:8]}...)"
                            )
                            await self._notify(token)
        except asyncio.TimeoutError:
            logger.debug("Pump.fun API timeout")
        except Exception as e:
            logger.debug(f"Pump.fun API error: {e}")

    async def _scan_raydium(self) -> None:
        """Monitor Raydium for new liquidity pools via RPC log subscription."""
        logger.info("Scanning Raydium for new pools...")
        while self.running:
            try:
                await self._poll_raydium_pools()
            except Exception as e:
                logger.error(f"Raydium scan error: {e}")
            await asyncio.sleep(self.config.scan_interval_ms / 1000)

    async def _poll_raydium_pools(self) -> None:
        """Poll Raydium for new pool creation via recent transactions."""
        if not self._session:
            return
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    RAYDIUM_AMM_V4,
                    {"limit": 5},
                ],
            }
            async with self._session.post(
                self.config.rpc_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    sigs = data.get("result", [])
                    for sig_info in sigs:
                        if sig_info.get("err") is None:
                            logger.debug(
                                f"Raydium tx: {sig_info.get('signature', '')[:16]}..."
                            )
        except asyncio.TimeoutError:
            logger.debug("Raydium RPC timeout")
        except Exception as e:
            logger.debug(f"Raydium poll error: {e}")

    async def _scan_jupiter(self) -> None:
        """Monitor Jupiter for new tradeable tokens."""
        logger.info("Scanning Jupiter for new tokens...")
        while self.running:
            try:
                await self._poll_jupiter_tokens()
            except Exception as e:
                logger.error(f"Jupiter scan error: {e}")
            await asyncio.sleep(self.config.scan_interval_ms / 1000 * 5)

    async def _poll_jupiter_tokens(self) -> None:
        """Poll Jupiter token list for new entries."""
        if not self._session:
            return
        try:
            url = "https://token.jup.ag/strict"
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    tokens = await resp.json()
                    logger.debug(f"Jupiter: {len(tokens)} tokens in strict list")
        except asyncio.TimeoutError:
            logger.debug("Jupiter API timeout")
        except Exception as e:
            logger.debug(f"Jupiter poll error: {e}")

    def get_recent_tokens(self, limit: int = 20) -> list[TokenInfo]:
        """Get recently detected tokens."""
        tokens = sorted(
            self.detected_tokens.values(),
            key=lambda t: t.detected_at,
            reverse=True,
        )
        return tokens[:limit]


def generate_simulated_tokens(count: int = 15) -> list[TokenInfo]:
    """Generate simulated token data for demo/testing."""
    names = [
        ("PEPE2", "Pepe 2.0"),
        ("BONK", "Bonk Inu"),
        ("DOGE", "DogeSol"),
        ("WOJAK", "Wojak Token"),
        ("MOON", "MoonShot"),
        ("CHAD", "GigaChad"),
        ("FROG", "Frog Nation"),
        ("ANDY", "Andy Token"),
        ("BRETT", "Brett Sol"),
        ("POPCAT", "Popcat"),
        ("MICHI", "Michi"),
        ("WEN", "Wen Token"),
        ("BOME", "Book of Meme"),
        ("SLERF", "Slerf"),
        ("MEW", "Cat in Dogs World"),
    ]

    platforms = [Platform.PUMPFUN, Platform.RAYDIUM, Platform.JUPITER]
    tokens: list[TokenInfo] = []

    for i in range(min(count, len(names))):
        symbol, name = names[i]
        age_minutes = random.randint(1, 120)
        created = datetime.utcnow() - timedelta(minutes=age_minutes)
        liq = random.uniform(2.0, 200.0)
        price_sol = random.uniform(0.0000001, 0.001)
        mcap = random.uniform(5000, 2_000_000)

        token = TokenInfo(
            mint=f"{''.join(random.choices('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', k=44))}",
            name=name,
            symbol=symbol,
            decimals=random.choice([6, 9]),
            platform=random.choice(platforms),
            initial_liquidity_sol=round(liq, 2),
            current_price_sol=price_sol,
            current_price_usd=price_sol * 170,
            market_cap_usd=round(mcap, 2),
            holder_count=random.randint(5, 5000),
            created_at=created,
            detected_at=created + timedelta(seconds=random.randint(1, 30)),
        )
        tokens.append(token)

    return tokens


def generate_simulated_positions() -> list[dict[str, Any]]:
    """Generate simulated position data for demo."""
    from models import Position, PositionStatus, RiskLevel

    positions_data = [
        {
            "symbol": "PEPE2",
            "name": "Pepe 2.0",
            "platform": Platform.PUMPFUN,
            "entry_sol": 0.0000045,
            "current_sol": 0.0000089,
            "amount": 22_000_000,
            "invested": 0.1,
            "status": PositionStatus.OPEN,
            "risk": RiskLevel.MEDIUM,
            "age_min": 35,
        },
        {
            "symbol": "BONK",
            "name": "Bonk Inu",
            "platform": Platform.RAYDIUM,
            "entry_sol": 0.00000012,
            "current_sol": 0.00000031,
            "amount": 800_000_000,
            "invested": 0.1,
            "status": PositionStatus.OPEN,
            "risk": RiskLevel.LOW,
            "age_min": 120,
        },
        {
            "symbol": "WOJAK",
            "name": "Wojak Token",
            "platform": Platform.PUMPFUN,
            "entry_sol": 0.0000002,
            "current_sol": 0.0000001,
            "amount": 500_000_000,
            "invested": 0.1,
            "status": PositionStatus.OPEN,
            "risk": RiskLevel.HIGH,
            "age_min": 15,
        },
        {
            "symbol": "FROG",
            "name": "Frog Nation",
            "platform": Platform.RAYDIUM,
            "entry_sol": 0.000001,
            "current_sol": 0.000005,
            "amount": 100_000_000,
            "invested": 0.1,
            "status": PositionStatus.TAKE_PROFIT,
            "risk": RiskLevel.SAFE,
            "age_min": 240,
        },
        {
            "symbol": "MOON",
            "name": "MoonShot",
            "platform": Platform.PUMPFUN,
            "entry_sol": 0.0000003,
            "current_sol": 0.00000005,
            "amount": 300_000_000,
            "invested": 0.1,
            "status": PositionStatus.STOPPED_OUT,
            "risk": RiskLevel.SCAM,
            "age_min": 60,
        },
    ]

    positions: list[dict[str, Any]] = []
    for p in positions_data:
        current_value = p["current_sol"] * p["amount"]
        pnl_sol = current_value - p["invested"]
        pnl_pct = (pnl_sol / p["invested"]) * 100 if p["invested"] > 0 else 0
        opened = datetime.utcnow() - timedelta(minutes=p["age_min"])

        pos = Position(
            id=f"pos-{len(positions) + 1}",
            token_mint=f"{''.join(random.choices('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', k=44))}",
            token_symbol=p["symbol"],
            token_name=p["name"],
            platform=p["platform"],
            entry_price_sol=p["entry_sol"],
            entry_price_usd=p["entry_sol"] * 170,
            current_price_sol=p["current_sol"],
            current_price_usd=p["current_sol"] * 170,
            amount_tokens=p["amount"],
            invested_sol=p["invested"],
            current_value_sol=round(current_value, 6),
            pnl_sol=round(pnl_sol, 6),
            pnl_pct=round(pnl_pct, 2),
            highest_price_sol=max(p["entry_sol"], p["current_sol"]) * random.uniform(1.0, 1.5),
            status=p["status"],
            risk_level=p["risk"],
            opened_at=opened,
            closed_at=datetime.utcnow() if p["status"] != PositionStatus.OPEN else None,
        )
        positions.append(pos.model_dump())

    return positions
