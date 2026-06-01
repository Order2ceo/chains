"""Live market data via the Jupiter token API.

Provides real token metadata (decimals, price, liquidity, holders, mcap) and a
feed of recently-created tokens for the scanner.
"""

from __future__ import annotations

import logging
import time

import aiohttp

from config import WSOL_MINT

logger = logging.getLogger(__name__)

TOKENS_BASE = "https://lite-api.jup.ag/tokens/v2"

_sol_price_cache: dict[str, float] = {"price": 0.0, "ts": 0.0}


async def get_sol_price_usd(session: aiohttp.ClientSession) -> float:
    """Return SOL/USD price, cached for 30s."""
    now = time.time()
    if _sol_price_cache["price"] and now - _sol_price_cache["ts"] < 30:
        return _sol_price_cache["price"]
    info = await get_token_market(WSOL_MINT, session)
    price = info.get("price_usd", 0.0) if info else 0.0
    if price:
        _sol_price_cache["price"] = price
        _sol_price_cache["ts"] = now
    return price or 0.0


async def get_token_market(mint: str, session: aiohttp.ClientSession) -> dict | None:
    """Fetch real market data for a single mint. Returns None if not found."""
    try:
        async with session.get(
            f"{TOKENS_BASE}/search", params={"query": mint}, timeout=10
        ) as r:
            if r.status != 200:
                return None
            arr = await r.json()
    except Exception as e:  # noqa: BLE001
        logger.error("get_token_market error for %s: %s", mint, e)
        return None

    match = next((t for t in arr if t.get("id") == mint), arr[0] if arr else None)
    if not match:
        return None
    return _normalize(match)


def _normalize(t: dict) -> dict:
    return {
        "mint": t.get("id"),
        "symbol": t.get("symbol", "?"),
        "name": t.get("name", "Unknown"),
        "decimals": int(t.get("decimals", 9)),
        "price_usd": float(t.get("usdPrice") or 0.0),
        "liquidity_usd": float(t.get("liquidity") or 0.0),
        "holders": int(t.get("holderCount") or 0),
        "mcap": float(t.get("mcap") or 0.0),
        "total_supply": float(t.get("totalSupply") or 0.0),
        "mint_authority_disabled": t.get("audit", {}).get("mintAuthorityDisabled"),
        "freeze_authority_disabled": t.get("audit", {}).get("freezeAuthorityDisabled"),
        "top_holders_pct": t.get("audit", {}).get("topHoldersPercentage"),
        "organic_score": t.get("organicScore"),
    }


async def get_recent_tokens(session: aiohttp.ClientSession) -> list[dict]:
    """Return recently-created tokens (for new-token sniping)."""
    try:
        async with session.get(f"{TOKENS_BASE}/recent", timeout=10) as r:
            if r.status != 200:
                return []
            arr = await r.json()
    except Exception as e:  # noqa: BLE001
        logger.error("get_recent_tokens error: %s", e)
        return []
    return [_normalize(t) for t in arr]


async def get_token_price_sol(
    mint: str, session: aiohttp.ClientSession
) -> tuple[float, dict | None]:
    """Return (price_in_SOL, market_dict) for a mint."""
    info = await get_token_market(mint, session)
    if not info:
        return 0.0, None
    sol_usd = await get_sol_price_usd(session)
    price_sol = info["price_usd"] / sol_usd if sol_usd else 0.0
    return price_sol, info
