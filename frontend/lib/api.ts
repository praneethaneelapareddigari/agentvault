const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export interface StepStatus {
  label: string;
  status: "pending" | "active" | "done" | "failed";
}

export interface AgentRequest {
  id: string;
  status: string;
  raw_prompt: string;
  parsed_intent?: Record<string, unknown>;
  steps?: StepStatus[];
}

export interface ExecutionPlan {
  id: string;
  request_id: string;
  protocol: string;
  chain: string;
  amount_usd: number;
  expected_apy: number;
  estimated_gas_usd: number;
  risk_score: number;
  policy_status: string;
  policy_reasons?: string[];
  simulation_status: string;
  simulation_result?: {
    success: boolean;
    warnings?: string[];
    failure_reason?: string | null;
  };
}

export interface TransactionResult {
  id: string;
  plan_id: string;
  tx_hash: string;
  chain: string;
  status: string;
  block_number: number;
  explorer_url?: string | null;
}

export interface WalletBalances {
  address: string;
  balances: Record<string, Record<string, number>>;
  total_usd: number;
}

export interface ActivityItem {
  id: string;
  event_type: string;
  detail: Record<string, unknown>;
  created_at: string;
}

export const DEMO_WALLET = "0xDEMO0000000000000000000000000000000001";

export const api = {
  createAgentRequest: (prompt: string, walletAddress?: string) =>
    request<AgentRequest>("/api/agent/request", {
      method: "POST",
      body: JSON.stringify({ prompt, wallet_address: walletAddress }),
    }),
  getAgentRequest: (id: string) => request<AgentRequest>(`/api/agent/request/${id}`),
  getPlan: (id: string) => request<ExecutionPlan>(`/api/agent/request/${id}/plan`),
  approve: (id: string) =>
    request<TransactionResult>(`/api/agent/request/${id}/approve`, { method: "POST" }),
  reject: (id: string) =>
    request<AgentRequest>(`/api/agent/request/${id}/reject`, { method: "POST" }),
  getBalances: (address: string) => request<WalletBalances>(`/api/wallet/${address}/balances`),
  getActivity: (userId: string) => request<ActivityItem[]>(`/api/activity/${userId}`),
  getActivityByWallet: (address: string) =>
    request<ActivityItem[]>(`/api/activity/by-wallet/${address}`),
};
