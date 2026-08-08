"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, WalletBalances, ActivityItem, DEMO_WALLET } from "@/lib/api";

export default function Dashboard() {
  const [wallet, setWallet] = useState<WalletBalances | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getBalances(DEMO_WALLET).then(setWallet).catch((e) => setError(String(e)));
    // user_id lookup is simplified for demo: activity endpoint keyed by
    // user id, but since this is a single-demo-wallet build we let the
    // agent page create the user record; on first load this may be empty.
  }, []);

  const chains = wallet ? Object.keys(wallet.balances) : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Dashboard</h1>
        <p className="text-muted text-sm">
          Permissioned AI execution: AI proposes, policy validates, you approve.
        </p>
      </div>

      {error && (
        <div className="card p-4 text-danger text-sm">
          Could not reach backend: {error}. Is the API running on{" "}
          <code>NEXT_PUBLIC_API_URL</code>?
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-5 md:col-span-1">
          <p className="text-muted text-xs uppercase tracking-wide mb-1">
            Total Portfolio
          </p>
          <p className="text-3xl font-semibold">
            {wallet ? `$${wallet.total_usd.toLocaleString()}` : "—"}
          </p>
          <p className="text-xs text-muted mt-2">{DEMO_WALLET}</p>
        </div>

        <div className="card p-5 md:col-span-2">
          <p className="text-muted text-xs uppercase tracking-wide mb-3">
            Chain Balances
          </p>
          <div className="grid grid-cols-3 gap-4">
            {chains.map((chain) => (
              <div key={chain}>
                <p className="text-sm font-medium capitalize mb-1">{chain}</p>
                {Object.entries(wallet!.balances[chain]).map(([asset, amount]) => (
                  <p key={asset} className="text-xs text-muted">
                    {amount} {asset}
                  </p>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card p-6 flex items-center justify-between">
        <div>
          <p className="font-medium mb-1">Ready to put your assets to work?</p>
          <p className="text-sm text-muted">
            Describe a goal in plain language — AgentVault's agent will plan,
            validate, and simulate before anything executes.
          </p>
        </div>
        <Link
          href="/agent"
          className="bg-accent hover:opacity-90 transition px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap"
        >
          Talk to Agent
        </Link>
      </div>

      <div className="card p-5">
        <p className="text-muted text-xs uppercase tracking-wide mb-3">
          Supported Chains &amp; Assets
        </p>
        <div className="flex flex-wrap gap-2 text-sm">
          {["Ethereum", "Base", "Arbitrum"].map((c) => (
            <span key={c} className="px-3 py-1 rounded-full bg-panel border border-border">
              {c}
            </span>
          ))}
          {["USDC", "DAI", "ETH"].map((a) => (
            <span key={a} className="px-3 py-1 rounded-full bg-panel border border-border text-muted">
              {a}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
