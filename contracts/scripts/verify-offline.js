/**
 * Drives the compiled bytecode against Hardhat's in-process EVM directly
 * via ethers, bypassing Hardhat's own solc-download step (blocked in this
 * sandbox's network allowlist). This exercises the exact same deploy +
 * deposit + execute + Aave-supply flow as test/PolicyVault.test.js.
 */
const hre = require("hardhat");
const fs = require("fs");
const path = require("path");
const assert = require("assert");

async function main() {
  const { ethers } = hre;
  const compiled = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "compiled.json"), "utf8"));

  const [owner, relayer, user] = await ethers.getSigners();

  async function deploy(name, args = []) {
    const factory = new ethers.ContractFactory(
      compiled[name].abi,
      compiled[name].bytecode,
      owner
    );
    const c = await factory.deploy(...args);
    await c.waitForDeployment();
    return c;
  }

  const usdc = await deploy("MockERC20");
  const pool = await deploy("MockAavePool");
  const vault = await deploy("PolicyVault", [relayer.address]);

  console.log("Deployed:");
  console.log("  MockERC20 (mUSDC):", await usdc.getAddress());
  console.log("  MockAavePool:", await pool.getAddress());
  console.log("  PolicyVault:", await vault.getAddress());

  await (await usdc.mint(user.address, ethers.parseUnits("1000", 6))).wait();

  // --- Test 1: real ERC20 deposit ---
  await (await usdc.connect(user).approve(await vault.getAddress(), ethers.parseUnits("500", 6))).wait();
  await (await vault.connect(user).depositERC20(await usdc.getAddress(), ethers.parseUnits("500", 6))).wait();
  const depositedBal = await vault.balances(user.address, await usdc.getAddress());
  assert.strictEqual(depositedBal.toString(), ethers.parseUnits("500", 6).toString());
  console.log("✔ Test 1 PASSED: real ERC20 deposit via approve + depositERC20");

  // --- Test 2: relayer-only execution enforced ---
  const poolIface = new ethers.Interface(compiled.MockAavePool.abi);
  const supplyData = poolIface.encodeFunctionData("supply", [
    await usdc.getAddress(),
    ethers.parseUnits("500", 6),
    user.address,
    0,
  ]);

  let reverted = false;
  try {
    await vault.connect(user).executeIfApproved(
      user.address, await pool.getAddress(), await usdc.getAddress(),
      ethers.parseUnits("500", 6), ethers.encodeBytes32String("plan1"), supplyData
    );
  } catch (e) {
    reverted = e.message.includes("PolicyVault: not relayer");
  }
  assert.ok(reverted, "expected revert: not relayer");
  console.log("✔ Test 2 PASSED: non-relayer cannot execute");

  // --- Test 3: non-allowlisted protocol rejected ---
  let rejected = false;
  try {
    await vault.connect(relayer).executeIfApproved(
      user.address, await pool.getAddress(), await usdc.getAddress(),
      ethers.parseUnits("500", 6), ethers.encodeBytes32String("plan1"), supplyData
    );
  } catch (e) {
    rejected = e.message.includes("PolicyVault: protocol not approved");
  }
  assert.ok(rejected, "expected revert: protocol not approved");
  console.log("✔ Test 3 PASSED: unallowlisted protocol rejected");

  // --- Test 4: real Aave-shaped supply() execution ---
  await (await vault.connect(owner).setProtocolApproval(await pool.getAddress(), true)).wait();
  const tx = await vault.connect(relayer).executeIfApproved(
    user.address, await pool.getAddress(), await usdc.getAddress(),
    ethers.parseUnits("500", 6), ethers.encodeBytes32String("plan1"), supplyData
  );
  const receipt = await tx.wait();
  assert.strictEqual(receipt.status, 1);

  const vaultBalAfter = await vault.balances(user.address, await usdc.getAddress());
  assert.strictEqual(vaultBalAfter.toString(), "0");

  const poolSupplied = await pool.supplied(user.address, await usdc.getAddress());
  assert.strictEqual(poolSupplied.toString(), ethers.parseUnits("500", 6).toString());

  const poolUsdcBal = await usdc.balanceOf(await pool.getAddress());
  assert.strictEqual(poolUsdcBal.toString(), ethers.parseUnits("500", 6).toString());

  console.log("✔ Test 4 PASSED: real on-chain execution — funds moved vault -> Aave-shaped pool");
  console.log("  tx hash:", receipt.hash);
  console.log("  block:", receipt.blockNumber);
  console.log("  gas used:", receipt.gasUsed.toString());

  // --- Test 5: cannot execute more than deposited balance ---
  let insufficientCaught = false;
  try {
    await vault.connect(relayer).executeIfApproved(
      user.address, await pool.getAddress(), await usdc.getAddress(),
      ethers.parseUnits("1", 6), ethers.encodeBytes32String("plan2"), supplyData
    );
  } catch (e) {
    insufficientCaught = e.message.includes("PolicyVault: insufficient balance");
  }
  assert.ok(insufficientCaught, "expected revert: insufficient balance");
  console.log("✔ Test 5 PASSED: cannot execute beyond deposited balance");

  console.log("\nALL 5 TESTS PASSED against a real, running EVM.");
}

main().catch((e) => {
  console.error("TEST SUITE FAILED:", e);
  process.exit(1);
});
