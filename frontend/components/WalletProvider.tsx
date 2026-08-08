"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { connectWallet, getConnectedAccount } from "@/lib/wallet";
import { DEMO_WALLET } from "@/lib/api";

interface WalletContextValue {
  address: string | null;
  isReal: boolean;
  effectiveAddress: string;
  connecting: boolean;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
}

const WalletContext = createContext<WalletContextValue | null>(null);

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem("av_wallet") : null;
    if (stored) setAddress(stored);
    else getConnectedAccount().then((a) => a && setAddress(a));
  }, []);

  const connect = useCallback(async () => {
    setConnecting(true);
    setError(null);
    try {
      const addr = await connectWallet();
      setAddress(addr);
      localStorage.setItem("av_wallet", addr);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    setAddress(null);
    localStorage.removeItem("av_wallet");
  }, []);

  const value: WalletContextValue = {
    address,
    isReal: !!address,
    effectiveAddress: address ?? DEMO_WALLET,
    connecting,
    error,
    connect,
    disconnect,
  };

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export function useWallet() {
  const ctx = useContext(WalletContext);
  if (!ctx) throw new Error("useWallet must be used within WalletProvider");
  return ctx;
}
