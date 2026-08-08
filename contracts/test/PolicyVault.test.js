const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PolicyVault (real ERC20 + Aave-shaped execution)", function () {
  async function deployFixture() {
    const [owner, relayer, user, attacker] = await ethers.getSigners();

    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const usdc = await MockERC20.deploy();

    const MockAavePool = await ethers.getContractFactory("MockAavePool");
    const pool = await MockAavePool.deploy();

    const PolicyVault = await ethers.getContractFactory("PolicyVault");
    const vault = await PolicyVault.deploy(relayer.address);

    // Fund the user with mock USDC, as if from a faucet.
    await usdc.mint(user.address, ethers.parseUnits("1000", 6));

    return { vault, usdc, pool, owner, relayer, user, attacker };
  }

  it("accepts real ERC20 deposits via approve + depositERC20", async function () {
    const { vault, usdc, user } = await deployFixture();

    await usdc.connect(user).approve(await vault.getAddress(), ethers.parseUnits("500", 6));
    await vault.connect(user).depositERC20(await usdc.getAddress(), ethers.parseUnits("500", 6));

    expect(await vault.balances(user.address, await usdc.getAddress())).to.equal(
      ethers.parseUnits("500", 6)
    );
    expect(await usdc.balanceOf(await vault.getAddress())).to.equal(ethers.parseUnits("500", 6));
  });

  it("only relayer can call executeIfApproved", async function () {
    const { vault, usdc, pool, user, attacker } = await deployFixture();
    const amount = ethers.parseUnits("500", 6);
    await usdc.connect(user).approve(await vault.getAddress(), amount);
    await vault.connect(user).depositERC20(await usdc.getAddress(), amount);

    const data = pool.interface.encodeFunctionData("supply", [
      await usdc.getAddress(),
      amount,
      user.address,
      0,
    ]);

    await expect(
      vault
        .connect(attacker)
        .executeIfApproved(
          user.address,
          await pool.getAddress(),
          await usdc.getAddress(),
          amount,
          ethers.encodeBytes32String("plan1"),
          data
        )
    ).to.be.revertedWith("PolicyVault: not relayer");
  });

  it("rejects execution against a non-allowlisted protocol", async function () {
    const { vault, usdc, pool, relayer, user } = await deployFixture();
    const amount = ethers.parseUnits("500", 6);
    await usdc.connect(user).approve(await vault.getAddress(), amount);
    await vault.connect(user).depositERC20(await usdc.getAddress(), amount);

    const data = pool.interface.encodeFunctionData("supply", [
      await usdc.getAddress(),
      amount,
      user.address,
      0,
    ]);

    await expect(
      vault
        .connect(relayer)
        .executeIfApproved(
          user.address,
          await pool.getAddress(),
          await usdc.getAddress(),
          amount,
          ethers.encodeBytes32String("plan1"),
          data
        )
    ).to.be.revertedWith("PolicyVault: protocol not approved");
  });

  it("executes a real Aave-shaped supply() once the pool is allowlisted", async function () {
    const { vault, usdc, pool, owner, relayer, user } = await deployFixture();
    const amount = ethers.parseUnits("500", 6);

    await usdc.connect(user).approve(await vault.getAddress(), amount);
    await vault.connect(user).depositERC20(await usdc.getAddress(), amount);
    await vault.connect(owner).setProtocolApproval(await pool.getAddress(), true);

    const data = pool.interface.encodeFunctionData("supply", [
      await usdc.getAddress(),
      amount,
      user.address,
      0,
    ]);

    await expect(
      vault
        .connect(relayer)
        .executeIfApproved(
          user.address,
          await pool.getAddress(),
          await usdc.getAddress(),
          amount,
          ethers.encodeBytes32String("plan1"),
          data
        )
    ).to.emit(vault, "Executed");

    // Vault balance is now zero — funds actually moved into the pool.
    expect(await vault.balances(user.address, await usdc.getAddress())).to.equal(0);
    // The mock Aave pool actually received and recorded the supply.
    expect(await pool.supplied(user.address, await usdc.getAddress())).to.equal(amount);
    expect(await usdc.balanceOf(await pool.getAddress())).to.equal(amount);
  });

  it("cannot execute more than the user's deposited balance", async function () {
    const { vault, usdc, pool, owner, relayer, user } = await deployFixture();
    const deposited = ethers.parseUnits("300", 6);
    const requested = ethers.parseUnits("500", 6);

    await usdc.connect(user).approve(await vault.getAddress(), deposited);
    await vault.connect(user).depositERC20(await usdc.getAddress(), deposited);
    await vault.connect(owner).setProtocolApproval(await pool.getAddress(), true);

    const data = pool.interface.encodeFunctionData("supply", [
      await usdc.getAddress(),
      requested,
      user.address,
      0,
    ]);

    await expect(
      vault
        .connect(relayer)
        .executeIfApproved(
          user.address,
          await pool.getAddress(),
          await usdc.getAddress(),
          requested,
          ethers.encodeBytes32String("plan1"),
          data
        )
    ).to.be.revertedWith("PolicyVault: insufficient balance");
  });

  it("only owner can update the protocol allowlist", async function () {
    const { vault, pool, user } = await deployFixture();
    await expect(
      vault.connect(user).setProtocolApproval(await pool.getAddress(), true)
    ).to.be.revertedWith("PolicyVault: not owner");
  });

  it("lets a user withdraw their own undeployed balance", async function () {
    const { vault, usdc, user } = await deployFixture();
    const amount = ethers.parseUnits("200", 6);
    await usdc.connect(user).approve(await vault.getAddress(), amount);
    await vault.connect(user).depositERC20(await usdc.getAddress(), amount);

    await vault.connect(user).withdraw(await usdc.getAddress(), amount);
    expect(await usdc.balanceOf(user.address)).to.equal(ethers.parseUnits("1000", 6));
  });
});
