"""Token security analyzer — rug-pull detection and risk scoring."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from config import BotConfig, TOKEN_PROGRAM
from models import RiskLevel, SecurityAnalysis

logger = logging.getLogger(__name__)


async def analyze_token(
    mint: str, config: BotConfig, rpc_session: aiohttp.ClientSession | None = None
) -> SecurityAnalysis:
    """Run full security analysis on a token."""
    analysis = SecurityAnalysis(mint=mint)
    warnings: list[str] = []
    passed: list[str] = []

    own_session = rpc_session is None
    if own_session:
        rpc_session = aiohttp.ClientSession()

    try:
        # 1. Check mint authority and freeze authority
        mint_info = await _get_mint_info(mint, config.rpc_url, rpc_session)
        if mint_info:
            if mint_info.get("mintAuthority") is None:
                analysis.mint_authority_revoked = True
                analysis.is_mintable = False
                passed.append("Mint authority revoked")
            else:
                warnings.append("Mint authority NOT revoked — token can be inflated")

            if mint_info.get("freezeAuthority") is None:
                analysis.freeze_authority_revoked = True
                passed.append("Freeze authority revoked")
            else:
                warnings.append("Freeze authority active — tokens can be frozen")

        # 2. Check top holders concentration
        holders = await _get_top_holders(mint, config.rpc_url, rpc_session)
        if holders:
            total_supply = sum(h["amount"] for h in holders)
            if total_supply > 0 and holders:
                analysis.top_holder_pct = (holders[0]["amount"] / total_supply) * 100
                top_10_sum = sum(h["amount"] for h in holders[:10])
                analysis.top_10_holder_pct = (top_10_sum / total_supply) * 100

                if analysis.top_holder_pct <= config.max_top_holder_pct:
                    passed.append(
                        f"Top holder owns {analysis.top_holder_pct:.1f}% (under {config.max_top_holder_pct}%)"
                    )
                else:
                    warnings.append(
                        f"Top holder owns {analysis.top_holder_pct:.1f}% — high concentration risk"
                    )

                analysis.supply_concentration = analysis.top_10_holder_pct

        # 3. Calculate risk score (0-100)
        score = 0
        if analysis.mint_authority_revoked:
            score += 25
        if analysis.freeze_authority_revoked:
            score += 20
        if analysis.top_holder_pct <= 20:
            score += 20
        elif analysis.top_holder_pct <= 40:
            score += 10
        if analysis.top_10_holder_pct <= 50:
            score += 10
        if analysis.liquidity_locked:
            score += 15
        if analysis.lp_burned_pct > 50:
            score += 10

        analysis.score = min(score, 100)

        # 4. Determine risk level
        if score >= 80:
            analysis.risk_level = RiskLevel.SAFE
        elif score >= 60:
            analysis.risk_level = RiskLevel.LOW
        elif score >= 40:
            analysis.risk_level = RiskLevel.MEDIUM
        elif score >= 20:
            analysis.risk_level = RiskLevel.HIGH
        else:
            analysis.risk_level = RiskLevel.SCAM

        # Honeypot heuristic
        analysis.has_honeypot_risk = analysis.score < 40

        analysis.warnings = warnings
        analysis.passed_checks = passed

    except Exception as e:
        logger.error(f"Error analyzing token {mint}: {e}")
        analysis.warnings = [f"Analysis failed: {str(e)}"]
    finally:
        if own_session and rpc_session:
            await rpc_session.close()

    return analysis


async def _get_mint_info(
    mint: str, rpc_url: str, session: aiohttp.ClientSession
) -> dict[str, Any] | None:
    """Get mint account info from Solana RPC."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                mint,
                {"encoding": "jsonParsed"},
            ],
        }
        async with session.post(rpc_url, json=payload) as resp:
            data = await resp.json()
            result = data.get("result", {})
            value = result.get("value")
            if value and value.get("data", {}).get("parsed"):
                return value["data"]["parsed"]["info"]
    except Exception as e:
        logger.error(f"Error getting mint info: {e}")
    return None


async def _get_top_holders(
    mint: str, rpc_url: str, session: aiohttp.ClientSession
) -> list[dict[str, Any]]:
    """Get largest token holders."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": [mint],
        }
        async with session.post(rpc_url, json=payload) as resp:
            data = await resp.json()
            result = data.get("result", {})
            accounts = result.get("value", [])
            return [
                {
                    "address": a["address"],
                    "amount": float(a.get("uiAmount", 0) or 0),
                }
                for a in accounts
            ]
    except Exception as e:
        logger.error(f"Error getting top holders: {e}")
    return []


def passes_safety_filters(
    analysis: SecurityAnalysis, config: BotConfig
) -> tuple[bool, list[str]]:
    """Check if a token passes safety filters. Returns (passed, reasons)."""
    failures: list[str] = []

    if config.require_renounced_mint and not analysis.mint_authority_revoked:
        failures.append("Mint authority not revoked")

    if config.require_no_freeze and not analysis.freeze_authority_revoked:
        failures.append("Freeze authority not revoked")

    if config.require_locked_liquidity and not analysis.liquidity_locked:
        failures.append("Liquidity not locked")

    if analysis.top_holder_pct > config.max_top_holder_pct:
        failures.append(
            f"Top holder {analysis.top_holder_pct:.1f}% > max {config.max_top_holder_pct}%"
        )

    if analysis.risk_level == RiskLevel.SCAM:
        failures.append("Token flagged as potential scam")

    return len(failures) == 0, failures
