import axios from "axios";
import type { BotConfig, DashboardData, Position, SecurityAnalysis, TokenInfo, Trade } from "./types";

const API = axios.create({ baseURL: "http://localhost:8001" });

export const fetchDashboard = async (): Promise<DashboardData> => {
  const { data } = await API.get("/api/dashboard");
  return data;
};

export const fetchTokens = async (limit = 20): Promise<TokenInfo[]> => {
  const { data } = await API.get(`/api/tokens?limit=${limit}`);
  return data;
};

export const fetchTokenAnalysis = async (mint: string): Promise<SecurityAnalysis> => {
  const { data } = await API.get(`/api/tokens/${mint}/analysis`);
  return data;
};

export const fetchPositions = async (): Promise<Position[]> => {
  const { data } = await API.get("/api/positions");
  return data;
};

export const fetchTrades = async (limit = 50): Promise<Trade[]> => {
  const { data } = await API.get(`/api/trades?limit=${limit}`);
  return data;
};

export const fetchConfig = async (): Promise<BotConfig> => {
  const { data } = await API.get("/api/config");
  return data;
};

export const updateConfig = async (update: Partial<BotConfig>): Promise<void> => {
  await API.post("/api/config", update);
};

export const manualBuy = async (mint: string) => {
  const { data } = await API.post(`/api/buy/${mint}`);
  return data;
};

export const manualSell = async (mint: string) => {
  const { data } = await API.post(`/api/sell/${mint}`);
  return data;
};

export const startScanner = async () => {
  const { data } = await API.post("/api/scanner/start");
  return data;
};

export const stopScanner = async () => {
  const { data } = await API.post("/api/scanner/stop");
  return data;
};
