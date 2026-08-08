const hre = require("hardhat");

async function main() {
  const relayer = process.env.RELAYER_ADDRESS;
  if (!relayer) {
    throw new Error("Set RELAYER_ADDRESS in your .env before deploying.");
  }

  const PolicyVault = await hre.ethers.getContractFactory("PolicyVault");
  const vault = await PolicyVault.deploy(relayer);
  await vault.waitForDeployment();

  console.log("PolicyVault deployed to:", await vault.getAddress());
  console.log("Relayer set to:", relayer);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
