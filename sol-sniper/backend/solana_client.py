"""Solana wallet + RPC client for live on-chain trading.

Wraps an async RPC connection and an optional signing keypair loaded from a
base58 private key. When no keypair/RPC is configured the bot stays in
read-only / dry-run mode.
"""

from __future__ import annotations

import logging

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature

logger = logging.getLogger(__name__)

LAMPORTS_PER_SOL = 1_000_000_000


class SolanaClient:
    """Manages the RPC connection and signing wallet."""

    def __init__(self, rpc_url: str, private_key: str | None = None):
        self.rpc_url = rpc_url
        self._client: AsyncClient | None = None
        self.keypair: Keypair | None = None
        if private_key:
            try:
                self.keypair = Keypair.from_base58_string(private_key.strip())
                logger.info(
                    "Wallet loaded: %s", str(self.keypair.pubkey())
                )
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to load wallet keypair: %s", e)
                self.keypair = None

    @property
    def client(self) -> AsyncClient:
        if self._client is None:
            self._client = AsyncClient(self.rpc_url, commitment=Confirmed)
        return self._client

    @property
    def has_wallet(self) -> bool:
        return self.keypair is not None

    @property
    def pubkey(self) -> Pubkey | None:
        return self.keypair.pubkey() if self.keypair else None

    @property
    def wallet_address(self) -> str | None:
        return str(self.keypair.pubkey()) if self.keypair else None

    async def get_sol_balance(self) -> float:
        """Return the wallet's SOL balance (0.0 if no wallet)."""
        if not self.keypair:
            return 0.0
        resp = await self.client.get_balance(self.keypair.pubkey())
        return (resp.value or 0) / LAMPORTS_PER_SOL

    async def get_token_balance(self, mint: str) -> float:
        """Return the raw UI token balance held by the wallet for `mint`."""
        if not self.keypair:
            return 0.0
        try:
            resp = await self.client.get_token_accounts_by_owner_json_parsed(
                self.keypair.pubkey(),
                {"mint": Pubkey.from_string(mint)},  # type: ignore[arg-type]
            )
            total = 0.0
            for acc in resp.value:
                info = acc.account.data.parsed["info"]
                total += float(info["tokenAmount"]["uiAmount"] or 0)
            return total
        except Exception as e:  # noqa: BLE001
            logger.error("get_token_balance error for %s: %s", mint, e)
            return 0.0

    async def confirm_signature(self, sig: Signature) -> bool:
        """Best-effort confirmation check for a transaction signature."""
        try:
            resp = await self.client.confirm_transaction(sig, commitment=Confirmed)
            val = resp.value[0] if resp.value else None
            return bool(val and val.err is None)
        except Exception as e:  # noqa: BLE001
            logger.error("confirm_transaction error: %s", e)
            return False

    def tx_opts(self) -> TxOpts:
        return TxOpts(skip_preflight=False, preflight_commitment=Confirmed)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
