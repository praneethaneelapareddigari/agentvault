"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWallet } from "@/components/WalletProvider";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/agent", label: "Agent" },
  { href: "/activity", label: "Activity" },
];

function short(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export default function Nav() {
  const pathname = usePathname();
  const { address, connecting, connect, disconnect } = useWallet();

  return (
    <header className="border-b border-border">
      <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center font-bold text-sm">
            AV
          </div>
          <span className="font-semibold tracking-tight">AgentVault</span>
        </div>

        <div className="flex items-center gap-4">
          <nav className="flex gap-1">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`px-3 py-1.5 rounded-lg text-sm transition ${
                  pathname === l.href
                    ? "bg-panel text-white border border-border"
                    : "text-muted hover:text-white"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </nav>

          {address ? (
            <button
              onClick={disconnect}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-panel border border-accent2 text-accent2"
              title="Click to disconnect"
            >
              ● {short(address)}
            </button>
          ) : (
            <button
              onClick={connect}
              disabled={connecting}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-accent hover:opacity-90 transition disabled:opacity-40"
            >
              {connecting ? "Connecting..." : "Connect Wallet"}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
