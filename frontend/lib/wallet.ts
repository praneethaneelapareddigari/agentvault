"use client";

/**
 * Real wallet connection via any EIP-1193 provider (MetaMask, Coinbase
 * Wallet, etc.) — no wallet-connect library dependency, just the standard
 * window.ethereum interface every browser wallet implements.
 */

export const BASE_SEPOLIA = {
  chainIdHex: "0x14a34", // 84532
  chainId: 84532,
  chainName: "Base Sepolia",
  rpcUrls: ["https://sepolia.base.org"],
  nativeCurrency: { name: "Sepolia Ether", symbol: "ETH", decimals: 18 },
  blockExplorerUrls: ["https://sepolia.basescan.org"],
};

function getProvider(): any {
  const eth = (window as any).ethereum;
  if (!eth) {
    throw new Error(
      "No wallet found. Install MetaMask (or another browser wallet) to connect."
    );
  }
  return eth;
}

export async function ensureBaseSepolia(): Promise<void> {
  const eth = getProvider();
  try {
    await eth.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: BASE_SEPOLIA.chainIdHex }],
    });
  } catch (switchError: any) {
    // 4902 = chain not added to the wallet yet
    if (switchError?.code === 4902) {
      await eth.request({
        method: "wallet_addEthereumChain",
        params: [
          {
            chainId: BASE_SEPOLIA.chainIdHex,
            chainName: BASE_SEPOLIA.chainName,
            rpcUrls: BASE_SEPOLIA.rpcUrls,
            nativeCurrency: BASE_SEPOLIA.nativeCurrency,
            blockExplorerUrls: BASE_SEPOLIA.blockExplorerUrls,
          },
        ],
      });
    } else {
      throw switchError;
    }
  }
}

export async function connectWallet(): Promise<string> {
  const eth = getProvider();
  const accounts: string[] = await eth.request({ method: "eth_requestAccounts" });
  if (!accounts?.length) throw new Error("No accounts returned by wallet.");
  await ensureBaseSepolia();
  return accounts[0];
}

export function getConnectedAccount(): Promise<string | null> {
  try {
    const eth = getProvider();
    return eth
      .request({ method: "eth_accounts" })
      .then((accounts: string[]) => accounts?.[0] ?? null)
      .catch(() => null);
  } catch {
    return Promise.resolve(null);
  }
}

/** Minimal manual ABI encoding for the two calls the deposit flow needs —
 * avoids pulling in a full web3 library just for two function calls. */
function encodeAddress(addr: string): string {
  return addr.toLowerCase().replace("0x", "").padStart(64, "0");
}
function encodeUint(value: bigint): string {
  return value.toString(16).padStart(64, "0");
}

/** ERC20 approve(address spender, uint256 amount) */
export function encodeApprove(spender: string, amount: bigint): string {
  return "0x095ea7b3" + encodeAddress(spender) + encodeUint(amount);
}

/** PolicyVault depositERC20(address token, uint256 amount) */
export function encodeDepositERC20(token: string, amount: bigint): string {
  // keccak256("depositERC20(address,uint256)")[:4] = 0x97feb926
  return "0x97feb926" + encodeAddress(token) + encodeUint(amount);
}

export async function sendTransaction(from: string, to: string, data: string): Promise<string> {
  const eth = getProvider();
  const txHash: string = await eth.request({
    method: "eth_sendTransaction",
    params: [{ from, to, data }],
  });
  return txHash;
}
