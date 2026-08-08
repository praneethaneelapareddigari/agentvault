const hre = require("hardhat");

// Aave V3 Pool Proxy — Base Sepolia (proto_base_sepolia_v3 market),
// verified on BaseScan: https://sepolia.basescan.org/address/0xA238Dd80C259a72e81d7e4664a9801593F98d1c5
const AAVE_POOL_BASE_SEPOLIA = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5";

async function main() {
  const relayer = process.env.RELAYER_ADDRESS;
  if (!relayer) {
    throw new Error("Set RELAYER_ADDRESS in your .env before deploying.");
  }

  const PolicyVault = await hre.ethers.getContractFactory("PolicyVault");
  const vault = await PolicyVault.deploy(relayer);
  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();

  console.log("PolicyVault deployed to:", vaultAddress);
  console.log("Relayer set to:", relayer);

  const aavePool = process.env.AAVE_POOL_ADDRESS || AAVE_POOL_BASE_SEPOLIA;
  const tx = await vault.setProtocolApproval(aavePool, true);
  await tx.wait();
  console.log("Allowlisted Aave Pool:", aavePool);

  console.log("\nSet these in backend/.env:");
  console.log(`POLICY_VAULT_ADDRESS=${vaultAddress}`);
  console.log(`AAVE_POOL_ADDRESS=${aavePool}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
