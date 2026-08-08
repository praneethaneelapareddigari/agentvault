"use client";

import { useEffect, useState } from "react";
import { api, ActivityItem, DEMO_WALLET } from "@/lib/api";

const HIDDEN_EVENT_PREFIX = "step:"; // step-by-step logs shown on the Agent page, not here

export default function ActivityPage() {
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getActivityByWallet(DEMO_WALLET)
      .then((all) => setItems(all.filter((i) => !i.event_type.startsWith(HIDDEN_EVENT_PREFIX))))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Activity</h1>
        <p className="text-muted text-sm">Full audit log of agent requests and executions.</p>
      </div>

      {error && <div className="card p-4 text-danger text-sm">{error}</div>}

      {items.length === 0 && !error && (
        <div className="card p-6 text-muted text-sm">
          No activity yet — run a request from the Agent page.
        </div>
      )}

      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.id} className="card p-4 flex items-start justify-between text-sm">
            <div>
              <p className="font-medium">{formatEventType(item.event_type)}</p>
              {item.detail && (
                <pre className="text-xs text-muted mt-1 whitespace-pre-wrap break-all">
                  {JSON.stringify(item.detail, null, 0)}
                </pre>
              )}
            </div>
            <span className="text-xs text-muted whitespace-nowrap ml-4">
              {new Date(item.created_at).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatEventType(t: string) {
  return t
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
