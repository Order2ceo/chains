"""Jupiter aggregator integration for real on-chain swaps.

Uses Jupiter's public swap API to fetch quotes and build swap transactions,
which are then signed locally with the bot wallet and submitted to the RPC.

API docs: https://dev.jup.ag/docs/swap-api/
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import aiohttp
from solders.transaction import VersionedTransaction

from config import WSOL_MINT
from solana_client import LAMPORTS_PER_SOL, SolanaClient

logger = logging.getLogger(__name__)

JUP_BASE = "https://lite-api.jup.ag/swap/v1"


@dataclass
class SwapResult:
    ok: bool
    tx_signature: str | None = None
    in_amount: float = 0.0  # UI amount of input
    out_amount: float = 0.0  # UI amount of output
    price_impact_pct: float = 0.0
    error: str | None = None


async def get_quote(
    input_mint: str,
    output_mint: str,
    amount_base_units: int,
    slippage_bps: int,
    session: aiohttp.ClientSession,
) -> dict | None:
    """Fetch a Jupiter quote. `amount_base_units` is in the input mint's base units."""
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(amount_base_units),
        "slippageBps": str(slippage_bps),
    }
    try:
        async with session.get(f"{JUP_BASE}/quote", params=params, timeout=15) as r:
            if r.status != 200:
                logger.error("Jupiter quote HTTP %s: %s", r.status, await r.text())
                return None
            return await r.json()
    except Exception as e:  # noqa: BLE001
        logger.error("Jupiter quote error: %s", e)
        return None


async def _execute_swap(
    quote: dict,
    sol: SolanaClient,
    session: aiohttp.ClientSession,
    priority_fee_lamports: int,
) -> SwapResult:
    """Build, sign and send a swap transaction for a given quote."""
    if not sol.has_wallet:
        return SwapResult(ok=False, error="No wallet configured")

    body = {
        "quoteResponse": quote,
        "userPublicKey": sol.wallet_address,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
        "prioritizationFeeLamports": priority_fee_lamports,
    }
    try:
        async with session.post(f"{JUP_BASE}/swap", json=body, timeout=20) as r:
            if r.status != 200:
                return SwapResult(
                    ok=False, error=f"swap build HTTP {r.status}: {await r.text()}"
                )
            data = await r.json()
        swap_tx_b64 = data["swapTransaction"]
    except Exception as e:  # noqa: BLE001
        return SwapResult(ok=False, error=f"swap build error: {e}")

    try:
        raw = base64.b64decode(swap_tx_b64)
        unsigned = VersionedTransaction.from_bytes(raw)
        signed = VersionedTransaction(unsigned.message, [sol.keypair])
        send_resp = await sol.client.send_raw_transaction(
            bytes(signed), opts=sol.tx_opts()
        )
        sig = send_resp.value
        confirmed = await sol.confirm_signature(sig)
        if not confirmed:
            return SwapResult(
                ok=False, tx_signature=str(sig), error="tx not confirmed"
            )
        return SwapResult(ok=True, tx_signature=str(sig))
    except Exception as e:  # noqa: BLE001
        return SwapResult(ok=False, error=f"sign/send error: {e}")


async def buy_token(
    mint: str,
    amount_sol: float,
    slippage_bps: int,
    sol: SolanaClient,
    session: aiohttp.ClientSession,
    priority_fee_lamports: int = 100_000,
) -> SwapResult:
    """Swap SOL -> token. Returns SwapResult with token out amount."""
    lamports = int(amount_sol * LAMPORTS_PER_SOL)
    quote = await get_quote(WSOL_MINT, mint, lamports, slippage_bps, session)
    if not quote:
        return SwapResult(ok=False, error="no route / quote failed")

    out_decimals = await _get_decimals(mint, session)
    out_ui = int(quote.get("outAmount", 0)) / (10**out_decimals)
    impact = float(quote.get("priceImpactPct", 0) or 0)

    res = await _execute_swap(quote, sol, session, priority_fee_lamports)
    res.in_amount = amount_sol
    res.out_amount = out_ui
    res.price_impact_pct = impact * 100
    return res


async def sell_token(
    mint: str,
    amount_tokens_base_units: int,
    slippage_bps: int,
    sol: SolanaClient,
    session: aiohttp.ClientSession,
    priority_fee_lamports: int = 100_000,
) -> SwapResult:
    """Swap token -> SOL. `amount_tokens_base_units` in the token's base units."""
    quote = await get_quote(
        mint, WSOL_MINT, amount_tokens_base_units, slippage_bps, session
    )
    if not quote:
        return SwapResult(ok=False, error="no route / quote failed")

    out_sol = int(quote.get("outAmount", 0)) / LAMPORTS_PER_SOL
    impact = float(quote.get("priceImpactPct", 0) or 0)

    res = await _execute_swap(quote, sol, session, priority_fee_lamports)
    res.out_amount = out_sol
    res.price_impact_pct = impact * 100
    return res


_DECIMALS_CACHE: dict[str, int] = {}


async def _get_decimals(mint: str, session: aiohttp.ClientSession) -> int:
    """Fetch token decimals via Jupiter token search API (cached)."""
    if mint in _DECIMALS_CACHE:
        return _DECIMALS_CACHE[mint]
    try:
        async with session.get(
            "https://lite-api.jup.ag/tokens/v2/search",
            params={"query": mint},
            timeout=10,
        ) as r:
            if r.status == 200:
                data = await r.json()
                for t in data:
                    if t.get("id") == mint:
                        dec = int(t.get("decimals", 9))
                        _DECIMALS_CACHE[mint] = dec
                        return dec
    except Exception as e:  # noqa: BLE001
        logger.error("decimals lookup error for %s: %s", mint, e)
    return 9
