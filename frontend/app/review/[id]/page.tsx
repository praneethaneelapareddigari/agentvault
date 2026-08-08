"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ExecutionPlan } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [plan, setPlan] = useState<ExecutionPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [explorerUrl, setExplorerUrl] = useState<string | null>(null);

  useEffect(() => {
    api.getPlan(id).then(setPlan).catch((e) => setError(String(e)));
  }, [id]);

  async function approve() {
    setBusy(true);
    try {
      const tx = await api.approve(id);
      const shortHash = `${tx.tx_hash.slice(0, 14)}...`;
      setResult(
        tx.explorer_url
          ? `Executed on-chain. Tx ${shortHash} on ${tx.chain} — status: ${tx.status}.`
          : `Executed. Tx ${shortHash} on ${tx.chain} — status: ${tx.status}.`
      );
      setExplorerUrl(tx.explorer_url ?? null);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function reject() {
    setBusy(true);
    try {
      await api.reject(id);
      router.push("/agent");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (error) return <div className="card p-4 text-danger text-sm">{error}</div>;
  if (!plan) return <div className="text-muted text-sm">Loading plan…</div>;

  const canApprove = plan.policy_status === "PASS" && plan.simulation_status === "PASS";

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Transaction Review</h1>
        <p className="text-muted text-sm">
          Nothing executes until you approve. This is the AI's proposal, not an action.
        </p>
      </div>

      <div className="card p-5 divide-y divide-border">
        <Row label="Action" value={`Deposit into ${plan.protocol}`} />
        <Row label="Amount" value={`$${plan.amount_usd}`} />
        <Row label="Chain" value={plan.chain} />
        <Row label="Protocol" value={plan.protocol} />
        <Row label="Expected APY" value={`${plan.expected_apy}%`} />
        <Row label="Estimated Gas" value={`$${plan.estimated_gas_usd}`} />
        <Row label="Risk Score" value={`${plan.risk_score}/100`} />
        <Row label="Policy" value={<StatusBadge status={plan.policy_status} />} raw />
        <Row
          label="Simulation"
          value={<StatusBadge status={plan.simulation_status} />}
          raw
        />
      </div>

      {plan.policy_reasons && plan.policy_reasons.length > 0 && (
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-muted mb-2">
            Policy Engine Notes
          </p>
          <ul className="text-sm space-y-1 list-disc list-inside">
            {plan.policy_reasons.map((r, i) => (
              <li key={i} className={plan.policy_status === "FAIL" ? "text-danger" : "text-muted"}>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {plan.simulation_result?.warnings && plan.simulation_result.warnings.length > 0 && (
        <div className="card p-4">
          <p className="text-xs uppercase tracking-wide text-muted mb-2">
            Simulation Warnings
          </p>
          <ul className="text-sm space-y-1 list-disc list-inside text-muted">
            {plan.simulation_result.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {result ? (
        <div className="card p-4 space-y-2">
          <p className="text-accent2 text-sm">{result}</p>
          {explorerUrl && (
            <a
              href={explorerUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-xs font-medium px-3 py-1.5 rounded-lg bg-panel border border-accent2 text-accent2 hover:opacity-80 transition"
            >
              View on BaseScan ↗
            </a>
          )}
        </div>
      ) : (
        <div className="flex gap-3">
          <button
            onClick={reject}
            disabled={busy}
            className="px-4 py-2 rounded-lg text-sm font-medium border border-border hover:bg-panel transition disabled:opacity-40"
          >
            Reject
          </button>
          <button
            onClick={approve}
            disabled={busy || !canApprove}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-accent hover:opacity-90 transition disabled:opacity-40"
            title={!canApprove ? "Plan failed policy or simulation checks" : ""}
          >
            {busy ? "Executing..." : "Approve"}
          </button>
        </div>
      )}
      {!canApprove && !result && (
        <p className="text-xs text-danger">
          This plan cannot be approved — it did not pass policy validation and/or simulation.
        </p>
      )}
    </div>
  );
}

function Row({
  label,
  value,
  raw,
}: {
  label: string;
  value: React.ReactNode;
  raw?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-3 text-sm">
      <span className="text-muted">{label}</span>
      {raw ? value : <span className="font-medium">{value}</span>}
    </div>
  );
}
