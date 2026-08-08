const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PolicyVault", function () {
  async function deployFixture() {
    const [owner, relayer, user, protocol, attacker] = await ethers.getSigners();
    const PolicyVault = await ethers.getContractFactory("PolicyVault");
    const vault = await PolicyVault.deploy(relayer.address);
    return { vault, owner, relayer, user, protocol, attacker };
  }

  it("accepts deposits and tracks user balance", async function () {
    const { vault, user } = await deployFixture();
    await vault.connect(user).deposit({ value: ethers.parseEther("1") });
    expect(await vault.balances(user.address)).to.equal(ethers.parseEther("1"));
  });

  it("only relayer can call executeIfApproved", async function () {
    const { vault, user, protocol, attacker } = await deployFixture();
    await vault.connect(user).deposit({ value: ethers.parseEther("1") });

    await expect(
      vault
        .connect(attacker)
        .executeIfApproved(
          user.address,
          protocol.address,
          ethers.parseEther("1"),
          ethers.encodeBytes32String("plan1"),
          "0x"
        )
    ).to.be.revertedWith("PolicyVault: not relayer");
  });

  it("rejects execution against a non-allowlisted protocol", async function () {
    const { vault, relayer, user, protocol } = await deployFixture();
    await vault.connect(user).deposit({ value: ethers.parseEther("1") });

    await expect(
      vault
        .connect(relayer)
        .executeIfApproved(
          user.address,
          protocol.address,
          ethers.parseEther("1"),
          ethers.encodeBytes32String("plan1"),
          "0x"
        )
    ).to.be.revertedWith("PolicyVault: protocol not approved");
  });

  it("executes successfully once protocol is allowlisted by owner", async function () {
    const { vault, owner, relayer, user, protocol } = await deployFixture();
    await vault.connect(user).deposit({ value: ethers.parseEther("1") });
    await vault.connect(owner).setProtocolApproval(protocol.address, true);

    await expect(
      vault
        .connect(relayer)
        .executeIfApproved(
          user.address,
          protocol.address,
          ethers.parseEther("1"),
          ethers.encodeBytes32String("plan1"),
          "0x"
        )
    ).to.emit(vault, "Executed");

    expect(await vault.balances(user.address)).to.equal(0);
  });

  it("only owner can update the protocol allowlist", async function () {
    const { vault, user, protocol } = await deployFixture();
    await expect(
      vault.connect(user).setProtocolApproval(protocol.address, true)
    ).to.be.revertedWith("PolicyVault: not owner");
  });
});
