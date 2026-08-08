"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, StepStatus } from "@/lib/api";

const EXAMPLE =
  "I have $1,000 USDC. Find a low-risk yield opportunity and invest $500, but don't spend more than $5 on gas and never put more than $500 into one protocol.";

function StepIcon({ status }: { status: StepStatus["status"] }) {
  if (status === "done") return <span className="text-accent2">●</span>;
  if (status === "failed") return <span className="text-danger">●</span>;
  if (status === "active") return <span className="text-accent animate-pulse">●</span>;
  return <span className="text-border">●</span>;
}

export default function AgentPage() {
  const [prompt, setPrompt] = useState(EXAMPLE);
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<StepStatus[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function submit() {
    setLoading(true);
    setError(null);
    setSteps(null);
    try {
      // Show a lightweight optimistic step list immediately, then replace
      // with the server's final step statuses once the (synchronous)
      // pipeline call resolves.
      setSteps([
        { label: "Understanding request", status: "active" },
        { label: "Analyzing wallet", status: "pending" },
        { label: "Searching protocols", status: "pending" },
        { label: "Comparing opportunities", status: "pending" },
        { label: "Checking risk", status: "pending" },
        { label: "Validating policy", status: "pending" },
        { label: "Simulating transaction", status: "pending" },
      ]);

      const req = await api.createAgentRequest(prompt);
      setSteps(req.steps ?? null);

      if (req.status === "awaiting_approval") {
        router.push(`/review/${req.id}`);
      } else if (req.status === "failed") {
        setError(
          "The agent couldn't find a viable opportunity matching your constraints. Try loosening risk, gas, or amount limits."
        );
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Agent Interface</h1>
        <p className="text-muted text-sm">
          Describe your goal. The agent proposes a plan — it never executes
          anything on its own.
        </p>
      </div>

      <div className="card p-5 space-y-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={4}
          className="w-full bg-bg border border-border rounded-lg p-3 text-sm outline-none focus:border-accent resize-none"
        />
        <button
          onClick={submit}
          disabled={loading || !prompt.trim()}
          className="bg-accent hover:opacity-90 transition px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-40"
        >
          {loading ? "Working..." : "Run Agent"}
        </button>
      </div>

      {error && <div className="card p-4 text-danger text-sm">{error}</div>}

      {steps && (
        <div className="card p-5 space-y-3">
          <p className="text-muted text-xs uppercase tracking-wide mb-2">
            Agent Status
          </p>
          {steps.map((s) => (
            <div key={s.label} className="flex items-center gap-3 text-sm">
              <StepIcon status={s.status} />
              <span className={s.status === "pending" ? "text-muted" : ""}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
