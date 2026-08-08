<div align="center">

# AgentVault

**Permissioned AI-agent execution layer for on-chain finance.**

Built for Hacker House Goa 2026 — AI × Crypto × Multichain.

</div>

<br/>

<div align="center">
<img src="docs/images/flow.png" width="100%" alt="AI proposes, Policy Engine validates, transaction simulated, user approves, smart wallet executes" />
</div>

<br/>

## Core thesis

AI agents should be able to act on-chain. Users should never have to give one unrestricted control over their assets.

That boundary — the AI can only *propose*; a deterministic, non-LLM **Policy Engine** decides what's *authorized*; the user gives final *approval* — is the entire product. It's a hard architectural separation, not a prompt instruction. See it for yourself in [`backend/app/engines/policy_engine.py`](backend/app/engines/policy_engine.py).

---

## Product tour

**Agent Interface** — describe a goal in plain language. The agent narrates its own progress; it never exposes raw chain-of-thought, and it never touches a wallet.

<img src="docs/images/agent-interface.png" width="100%" alt="Agent Interface screen" />

**Transaction Review** — the decision moment. Every field the Policy Engine checked, and why it passed or failed, laid out before you click anything.

<img src="docs/images/transaction-review.png" width="100%" alt="Transaction Review screen" />

**Dashboard** — portfolio, chain balances, and the entry point into the agent, at a glance.

<img src="docs/images/dashboard.png" width="100%" alt="Dashboard screen" />

---

## Architecture

<img src="docs/images/architecture.png" width="100%" alt="AgentVault system architecture diagram" />

```
agentvault/
├── backend/          FastAPI service: agents, engines, routers, tests
├── frontend/          Next.js + TypeScript + Tailwind UI
├── contracts/          Solidity fallback smart wallet (Hardhat project)
└── docker-compose.yml   Full local stack (Postgres + Redis + backend + frontend)
```

This is a **working, testable, demo-ready build**, not a slide deck. The full pipeline — natural language → intent → plan → risk score → policy check → simulation → approval → execution → verification — runs end-to-end today, backed by 17 passing backend tests and 7 passing contract tests. It runs entirely on mocks with zero setup, **or** it can send a real, signed transaction on Base Sepolia through a real deployed contract into Aave's real testnet Pool — same code path, one environment variable (see "Two execution modes" below).

---

## Quickstart

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: add ANTHROPIC_API_KEY for LLM-based intent parsing
uvicorn app.main:app --reload
# -> http://localhost:8000  (docs at /docs)
```

Run the test suite:

```bash
python3 -m pytest -v
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
# -> http://localhost:3000
```

### Everything via Docker

```bash
docker compose up --build
```

(Docker Compose targets Postgres for a production-shaped setup; the backend defaults to SQLite for zero-setup local dev — just change `DATABASE_URL`.)

### Smart contract

```bash
cd contracts
npm install
npx hardhat test
```

That test suite deploys `PolicyVault` against a real running EVM alongside a mintable mock USDC and a mock Aave pool matching Aave's actual `supply()` signature, then exercises the full deposit → relayer-only execution → allowlist enforcement → real fund movement flow — 7 tests, all real transactions on a real (local) chain, not assertions against mocked function calls.

To deploy to the actual Base Sepolia testnet, see "Real on-chain execution" below.

---

## The hero demo, end to end

1. Open the **Agent** page, submit:
   > "I have $1,000 USDC. Find a low-risk yield opportunity and invest $500, but don't spend more than $5 on gas and never put more than $500 into one protocol."
2. Watch the step tracker: Understanding request → Analyzing wallet → Searching protocols → Comparing opportunities → Checking risk → Validating policy → Simulating transaction.
3. You're routed to **Transaction Review**: protocol, chain, amount, expected APY, gas, risk score, policy PASS/FAIL, simulation PASS/FAIL.
4. Click **Approve** (or **Reject** — nothing happens without your click).
5. Executed transaction hash + confirmation shown; entry appears in **Activity**.

---

## Two execution modes

AgentVault ships with a toggle, `EXECUTION_MODE`, rather than a single hardcoded path:

| | `EXECUTION_MODE=mock` (default) | `EXECUTION_MODE=real` |
|---|---|---|
| Wallet balances | Hardcoded per-chain balances | Live Base Sepolia RPC reads (native ETH + USDC `balanceOf`) |
| Transaction simulation | Deterministic pseudo-random result | Real `eth_call` against Base Sepolia — asks the chain "would this Aave `supply()` revert?" with no gas spent |
| Execution | Mocked relayer call, fake tx hash | Backend relayer signs and broadcasts a real transaction calling `PolicyVault.executeIfApproved()`, which itself calls Aave V3 `Pool.supply()` — you get back a real tx hash and a BaseScan link |

Mock mode requires zero setup and is what runs out of the box — useful for iterating on the agent/policy logic without needing testnet funds every time. Real mode requires an RPC URL, a funded relayer key, and a deployed `PolicyVault` — see below.

**The security model doesn't change between modes.** Policy Engine, Risk Engine, and the approval gate are identical, deterministic, unit-tested code either way — `EXECUTION_MODE` only decides what happens *after* a plan has already passed every check and the user has clicked Approve.

### Setting up real execution

1. **Get a Base Sepolia RPC URL** — free tier from [Alchemy](https://www.alchemy.com/) or [Infura](https://www.infura.io/), or use the public endpoint `https://sepolia.base.org`.
2. **Create a relayer wallet** — a fresh address used *only* by the backend to sign `executeIfApproved()` calls. Fund it with a small amount of Base Sepolia ETH for gas from the [Alchemy faucet](https://www.alchemy.com/faucets/base-sepolia). Never use a wallet holding real funds.
3. **Get testnet USDC** for the Aave Base Sepolia market from the [Aave testnet faucet](https://bridge-testnet.aave.com/faucet/?marketName=proto_base_sepolia_v3) — note the USDC token address it gives you.
4. **Deploy `PolicyVault`**:
   ```bash
   cd contracts
   npm install
   cp .env.example .env   # fill in BASE_SEPOLIA_RPC_URL, DEPLOYER_PRIVATE_KEY, RELAYER_ADDRESS
   npm run deploy:base-sepolia
   ```
   This deploys the vault and automatically allowlists Aave's Pool contract. Copy the printed `POLICY_VAULT_ADDRESS`.
5. **Configure the backend** (`backend/.env`):
   ```
   EXECUTION_MODE=real
   BASE_SEPOLIA_RPC_URL=<your RPC URL>
   RELAYER_PRIVATE_KEY=<your relayer's private key>
   POLICY_VAULT_ADDRESS=<from step 4>
   USDC_ADDRESS_BASE_SEPOLIA=<from step 3>
   ```
6. **Configure the frontend** (`frontend/.env.local`) so the "Deposit to Vault" flow can build the right calldata:
   ```
   NEXT_PUBLIC_USDC_ADDRESS_BASE_SEPOLIA=<from step 3>
   NEXT_PUBLIC_POLICY_VAULT_ADDRESS=<from step 4>
   ```
7. Restart both servers, connect a wallet (MetaMask) from the nav bar — it'll prompt you to switch to Base Sepolia automatically — deposit some USDC to the vault (two signed transactions: approve + depositERC20), then run the hero demo prompt. Approving the plan now sends a real transaction; the confirmation screen links straight to BaseScan.

### What's still intentionally scoped down

| Component | Current build | Possible extension |
|---|---|---|
| Protocol yield data | Small hand-vetted allowlist (`services/protocol_data.py`) — one real integration (Aave), not fifteen | Live protocol APIs / DefiLlama per chain, still filtered through the same allowlist |
| DeFi protocols supported | Aave V3 only | Additional allowlisted protocols behind the same Risk Engine gate |
| Simulation depth | Single `eth_call` revert check | Full Tenderly simulation (state diffs, gas profiling) |

This is a deliberate hackathon scope decision, not a shortcut around the "did a real transaction happen" question — one protocol, fully real end to end, beats fifteen protocols that are all mocked.

---

## Security model

See [`backend/app/engines/policy_engine.py`](backend/app/engines/policy_engine.py).

- The LLM (Intent Agent, Planning Agent) never executes anything and never sees a private key.
- Every proposed plan passes through the Policy Engine — a small, dependency-free, 100%-deterministic module — before it can be simulated or approved.
- Every transaction, regardless of size, requires an explicit user `approve` call. There is no silent-execution path.
- The Risk Engine only scores protocols on a hand-vetted allowlist; anything else scores 0 and is rejected downstream.
- **`PolicyVault.sol` adds a second, independent, on-chain enforcement layer.** Even if the backend or the relayer's private key were fully compromised, an attacker still can't move a user's funds anywhere they want — `executeIfApproved()` only allows moving a user's *own deposited balance* into a protocol the (separately-keyed) owner has explicitly allowlisted on-chain. Attacker → backend → smart contract → **rejected**, verified by the `PolicyVault (real ERC20 + Aave-shaped execution)` test suite in `contracts/test/PolicyVault.test.js`, which deploys the real contract against a real EVM and asserts exactly this.

## Multichain scope

Ethereum, Base, and Arbitrum balances are readable; the live opportunity-discovery + execution demo path is **Base-first** for reliability (cheap, fast finality). This was a deliberate scope cut — see the architecture discussion for the full reasoning.

## What NOT to build (scope guardrails)

Not a chatbot, not a trading bot, not an NFT marketplace, not a 20-chain wallet, not an unrestricted autonomous agent. Every addition should be checked against: *does this materially improve the core AgentVault experience or Hacker House Goa selection potential?* If not, cut it.
