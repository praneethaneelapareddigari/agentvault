// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title PolicyVault
 * @notice Fallback smart-wallet contract for AgentVault (see architecture
 *         doc option 3). Holds user deposits and executes only through a
 *         single restricted entrypoint callable exclusively by the backend
 *         relayer address — which itself only calls this function AFTER a
 *         plan has passed the off-chain Policy Engine + Simulator, and the
 *         user has explicitly approved it via the UI.
 *
 *         This contract deliberately does NOT grant the relayer (or
 *         anything else) unrestricted call access — it can only move a
 *         user's own deposited balance to a pre-approved target contract,
 *         up to the amount the user deposited. It cannot be used to drain
 *         funds to an arbitrary address chosen at call time by the relayer
 *         alone; the target must be present in `approvedProtocols`.
 *
 *         Owner (the contract deployer / AgentVault operator) manages the
 *         protocol allowlist. Relayer role is separate from owner so a
 *         compromised relayer key cannot rewrite the allowlist itself.
 */
contract PolicyVault {
    address public owner;
    address public relayer;

    mapping(address => uint256) public balances; // user => deposited amount (native/ERC20-agnostic demo uses a simple ledger)
    mapping(address => bool) public approvedProtocols;

    event Deposited(address indexed user, uint256 amount);
    event Executed(address indexed user, address indexed protocol, uint256 amount, bytes32 planId);
    event ProtocolAllowlisted(address indexed protocol, bool allowed);
    event RelayerUpdated(address indexed newRelayer);

    modifier onlyOwner() {
        require(msg.sender == owner, "PolicyVault: not owner");
        _;
    }

    modifier onlyRelayer() {
        require(msg.sender == relayer, "PolicyVault: not relayer");
        _;
    }

    constructor(address _relayer) {
        owner = msg.sender;
        relayer = _relayer;
    }

    /// @notice Users deposit funds under their own control.
    function deposit() external payable {
        require(msg.value > 0, "PolicyVault: zero deposit");
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /// @notice Owner manages which downstream protocol contracts are
    /// eligible execution targets. This is the on-chain half of the
    /// allowlist enforced off-chain by the Risk Engine.
    function setProtocolApproval(address protocol, bool allowed) external onlyOwner {
        approvedProtocols[protocol] = allowed;
        emit ProtocolAllowlisted(protocol, allowed);
    }

    function setRelayer(address newRelayer) external onlyOwner {
        relayer = newRelayer;
        emit RelayerUpdated(newRelayer);
    }

    /**
     * @notice Executes a user's pre-approved plan.
     * @dev Callable only by the relayer, which itself only calls this after
     *      the off-chain Policy Engine + Simulator + explicit user approval
     *      have all passed. `protocol` must be on the on-chain allowlist,
     *      giving a second, independent enforcement point beyond the
     *      off-chain checks (defense in depth).
     * @param user The user whose deposited balance is being deployed.
     * @param protocol The pre-approved target contract (e.g. a lending pool).
     * @param amount Amount to deploy, must not exceed the user's balance.
     * @param planId Off-chain plan id, emitted for audit-log correlation.
     * @param data Calldata forwarded to the protocol contract.
     */
    function executeIfApproved(
        address user,
        address protocol,
        uint256 amount,
        bytes32 planId,
        bytes calldata data
    ) external onlyRelayer {
        require(approvedProtocols[protocol], "PolicyVault: protocol not approved");
        require(balances[user] >= amount, "PolicyVault: insufficient balance");

        balances[user] -= amount;

        (bool success, ) = protocol.call{value: amount}(data);
        require(success, "PolicyVault: execution failed");

        emit Executed(user, protocol, amount, planId);
    }

    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "PolicyVault: insufficient balance");
        balances[msg.sender] -= amount;
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "PolicyVault: withdraw failed");
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }
}
