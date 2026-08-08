## scripts/compile-with-npm-solc.js + scripts/verify-offline.js

These exist for one reason: Hardhat's default `compile`/`test` tasks download
the solc binary from `binaries.soliditylang.org` on first run. In network-
restricted CI environments (including the sandbox this project was
originally built in) that host may not be reachable, which makes
`npx hardhat test` fail with `HH502` even though the contracts themselves
are fine.

On your own machine, with normal internet access, you almost certainly
don't need these — just run:

```bash
npm install
npx hardhat test
```

If you ever hit `HH502: Couldn't download compiler version list` (e.g. in a
locked-down CI runner), this pair of scripts is the fallback: it compiles
via the pure-JS `solc` npm package instead of Hardhat's native downloader,
then deploys and exercises the compiled bytecode directly against Hardhat's
local EVM via ethers — covering the same deposit → execute → Aave-shaped
`supply()` flow as `test/PolicyVault.test.js`.

```bash
npm install --no-save solc@0.8.24
node scripts/compile-with-npm-solc.js
npx hardhat run scripts/verify-offline.js --network hardhat --no-compile
```
