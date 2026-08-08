import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import { WalletProvider } from "@/components/WalletProvider";

export const metadata: Metadata = {
  title: "AgentVault",
  description: "Permissioned AI-agent execution layer for on-chain finance.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg text-white">
        <WalletProvider>
          <Nav />
          <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
        </WalletProvider>
      </body>
    </html>
  );
}
