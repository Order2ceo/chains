import axios from "axios";
import type { StrategyResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchStrategyData(
  numCandles: number = 500
): Promise<StrategyResponse> {
  const response = await axios.get<StrategyResponse>(
    `${API_BASE}/api/strategy`,
    { params: { num_candles: numCandles } }
  );
  return response.data;
}
