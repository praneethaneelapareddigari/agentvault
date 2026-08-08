"use client";

import { useState } from "react";
import { encodeApprove, encodeDepositERC20, sendTransaction } from "@/lib/wallet";

const USDC_ADDRESS = process.env.NEXT_PUBLIC_USDC_ADDRESS_BASE_SEPOLIA || "";
const POLICY_VAULT_ADDRESS = process.env.NEXT_PUBLIC_POLICY_VAULT_ADDRESS || "";

/**
 * Two real, wallet-signed transactions on Base Sepolia:
 *   1. USDC.approve(vault, amount)
 *   2. PolicyVault.depositERC20(USDC, amount)
 *
 * Only rendered when a real wallet is connected. If the contract addresses
 * aren't configured (NEXT_PUBLIC_USDC_ADDRESS_BASE_SEPOLIA /
 * NEXT_PUBLIC_POLICY_VAULT_ADDRESS), shows setup instructions instead of a
 * broken form — see README "Real on-chain execution" section.
 */
export default function DepositPanel({ walletAddress }: { walletAddress: string }) {
  const [amount, setAmount] = useState("500");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const configured = !!USDC_ADDRESS && !!POLICY_VAULT_ADDRESS;

  async function depositToVault() {
    setBusy(true);
    setError(null);
    try {
      const amountWei = BigInt(Math.round(parseFloat(amount) * 1_000_000)); // USDC, 6 decimals

      setStatus("Waiting for approve() confirmation in your wallet...");
      const approveData = encodeApprove(POLICY_VAULT_ADDRESS, amountWei);
      const approveTx = await sendTransaction(walletAddress, USDC_ADDRESS, approveData);
      setStatus(`Approve sent (${approveTx.slice(0, 10)}...). Waiting for depositERC20()...`);

      const depositData = encodeDepositERC20(USDC_ADDRESS, amountWei);
      const depositTx = await sendTransaction(walletAddress, POLICY_VAULT_ADDRESS, depositData);
      setStatus(`Deposited. Tx: ${depositTx}`);
    } catch (e: any) {
      setError(e?.message ?? String(e));
      setStatus(null);
    } finally {
      setBusy(false);
    }
  }

  if (!configured) {
    return (
      <div className="card p-4 text-xs text-muted space-y-1">
        <p className="text-accent2 font-medium">Real wallet connected.</p>
        <p>
          To deposit real testnet USDC into the vault, set{" "}
          <code>NEXT_PUBLIC_USDC_ADDRESS_BASE_SEPOLIA</code> and{" "}
          <code>NEXT_PUBLIC_POLICY_VAULT_ADDRESS</code> in{" "}
          <code>frontend/.env.local</code> — see the README's "Real
          on-chain execution" section.
        </p>
      </div>
    );
  }

  return (
    <div className="card p-4 space-y-3">
      <p className="text-xs text-accent2 font-medium">
        Real wallet connected — deposit USDC to the PolicyVault (2 signed txs)
      </p>
      <div className="flex gap-2 items-center">
        <input
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          type="number"
          className="bg-bg border border-border rounded-lg px-3 py-2 text-sm w-32 outline-none focus:border-accent"
        />
        <span className="text-xs text-muted">USDC</span>
        <button
          onClick={depositToVault}
          disabled={busy}
          className="ml-auto px-3 py-2 rounded-lg text-xs font-medium bg-accent hover:opacity-90 transition disabled:opacity-40"
        >
          {busy ? "Confirming..." : "Deposit to Vault"}
        </button>
      </div>
      {status && <p className="text-xs text-muted break-all">{status}</p>}
      {error && <p className="text-xs text-danger break-all">{error}</p>}
    </div>
  );
}
