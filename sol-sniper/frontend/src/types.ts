export type Platform = "pumpfun" | "raydium" | "jupiter" | "orca";
export type RiskLevel = "safe" | "low" | "medium" | "high" | "scam";
export type TradeAction = "buy" | "sell";
export type TradeStatus = "pending" | "confirmed" | "failed";
export type PositionStatus = "open" | "closed" | "stopped_out" | "take_profit";

export interface WalletStatus {
  connected: boolean;
  address: string | null;
  sol_balance: number;
  rpc_configured: boolean;
  live_mode: boolean;
  is_live: boolean;
}

export interface LiveModeResponse {
  status: string;
  error?: string;
  live_mode: boolean;
  is_live: boolean;
}

export interface TokenInfo {
  mint: string;
  name: string;
  symbol: string;
  decimals: number;
  platform: Platform;
  pool_address: string;
  initial_liquidity_sol: number;
  current_price_sol: number;
  current_price_usd: number;
  market_cap_usd: number;
  holder_count: number;
  created_at: string;
  detected_at: string;
}

export interface SecurityAnalysis {
  mint: string;
  risk_level: RiskLevel;
  score: number;
  mint_authority_revoked: boolean;
  freeze_authority_revoked: boolean;
  liquidity_locked: boolean;
  top_holder_pct: number;
  top_10_holder_pct: number;
  has_honeypot_risk: boolean;
  is_mintable: boolean;
  warnings: string[];
  passed_checks: string[];
}

export interface Trade {
  id: string;
  token_mint: string;
  token_symbol: string;
  action: TradeAction;
  amount_sol: number;
  amount_tokens: number;
  price_sol: number;
  price_usd: number;
  tx_signature: string;
  status: TradeStatus;
  platform: Platform;
  timestamp: string;
}

export interface Position {
  id: string;
  token_mint: string;
  token_symbol: string;
  token_name: string;
  platform: Platform;
  entry_price_sol: number;
  entry_price_usd: number;
  current_price_sol: number;
  current_price_usd: number;
  amount_tokens: number;
  invested_sol: number;
  current_value_sol: number;
  pnl_sol: number;
  pnl_pct: number;
  highest_price_sol: number;
  status: PositionStatus;
  buy_tx: string;
  sell_tx: string;
  risk_level: RiskLevel;
  opened_at: string;
  closed_at: string | null;
}

export interface BotStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_invested_sol: number;
  total_returned_sol: number;
  total_pnl_sol: number;
  total_pnl_pct: number;
  best_trade_pnl_pct: number;
  worst_trade_pnl_pct: number;
  open_positions: number;
  sol_balance: number;
  wallet_address: string;
}

export interface DashboardData {
  stats: BotStats;
  positions: Position[];
  recent_tokens: TokenInfo[];
  recent_trades: Trade[];
  scanner_active: boolean;
  auto_buy_enabled: boolean;
  auto_sell_enabled: boolean;
}

export interface BotConfig {
  buy_amount_sol: number;
  max_buy_amount_sol: number;
  take_profit_pct: number;
  stop_loss_pct: number;
  trailing_stop_pct: number;
  slippage_bps: number;
  min_liquidity_sol: number;
  max_token_age_seconds: number;
  auto_buy_enabled: boolean;
  auto_sell_enabled: boolean;
  max_concurrent_positions: number;
  require_locked_liquidity: boolean;
  require_renounced_mint: boolean;
  require_no_freeze: boolean;
  platforms: string[];
  scanner_active: boolean;
}

export interface WsMessage {
  event: string;
  data: unknown;
  timestamp: string;
}
