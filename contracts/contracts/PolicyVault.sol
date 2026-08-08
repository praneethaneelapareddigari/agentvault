// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title PolicyVault
 * @notice Real smart-wallet contract for AgentVault. Holds user-deposited
 *         ERC20 balances (e.g. USDC) and moves them into a pre-approved
 *         DeFi protocol (e.g. Aave V3's Pool) ONLY through a single
 *         restricted entrypoint, callable exclusively by the backend
 *         relayer — and the relayer only calls it after the off-chain
 *         Policy Engine + Simulator + explicit user approval have all
 *         passed (see backend/app/engines/policy_engine.py).
 *
 *         This is the second, independent enforcement layer described in
 *         the security model: even a fully compromised backend/relayer key
 *         can only move a user's own deposited funds into a protocol the
 *         (separately-keyed) owner has explicitly allowlisted — it cannot
 *         redirect funds to an arbitrary attacker-chosen address.
 *
 *         Targets Aave V3's Pool contract on Base Sepolia:
 *         0xA238Dd80C259a72e81d7e4664a9801593F98d1c5
 *         (verified on BaseScan: proto_base_sepolia_v3 market)
 */
contract PolicyVault {
    address public owner;
    address public relayer;

    // user => token => balance
    mapping(address => mapping(address => uint256)) public balances;
    mapping(address => bool) public approvedProtocols;

    event Deposited(address indexed user, address indexed token, uint256 amount);
    event Executed(
        address indexed user,
        address indexed protocol,
        address indexed token,
        uint256 amount,
        bytes32 planId
    );
    event ProtocolAllowlisted(address indexed protocol, bool allowed);
    event RelayerUpdated(address indexed newRelayer);
    event Withdrawn(address indexed user, address indexed token, uint256 amount);

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

    /// @notice User deposits an ERC20 (e.g. USDC) under their own control.
    /// @dev Requires the user to have already called
    ///      token.approve(vaultAddress, amount) from their own wallet.
    function depositERC20(address token, uint256 amount) external {
        require(amount > 0, "PolicyVault: zero deposit");
        require(
            IERC20(token).transferFrom(msg.sender, address(this), amount),
            "PolicyVault: transferFrom failed"
        );
        balances[msg.sender][token] += amount;
        emit Deposited(msg.sender, token, amount);
    }

    /// @notice Owner manages which downstream protocol contracts are
    /// eligible execution targets — the on-chain half of the allowlist
    /// enforced off-chain by the Risk Engine.
    function setProtocolApproval(address protocol, bool allowed) external onlyOwner {
        approvedProtocols[protocol] = allowed;
        emit ProtocolAllowlisted(protocol, allowed);
    }

    function setRelayer(address newRelayer) external onlyOwner {
        relayer = newRelayer;
        emit RelayerUpdated(newRelayer);
    }

    /**
     * @notice Executes a user's pre-approved plan against an allowlisted
     *         DeFi protocol (e.g. Aave V3 Pool.supply()).
     * @param user Whose deposited balance is being deployed.
     * @param protocol Pre-approved target contract; reverts if not allowlisted.
     * @param token The ERC20 being deployed (e.g. USDC).
     * @param amount Amount to deploy; must not exceed the user's deposited balance.
     * @param planId Off-chain plan id, emitted for audit-log correlation.
     * @param data Calldata forwarded to the protocol (e.g. encoded Aave supply()).
     */
    function executeIfApproved(
        address user,
        address protocol,
        address token,
        uint256 amount,
        bytes32 planId,
        bytes calldata data
    ) external onlyRelayer {
        require(approvedProtocols[protocol], "PolicyVault: protocol not approved");
        require(balances[user][token] >= amount, "PolicyVault: insufficient balance");

        balances[user][token] -= amount;

        // Aave (and most lending protocols) pull funds via transferFrom,
        // so the vault must approve the protocol before calling it.
        require(IERC20(token).approve(protocol, amount), "PolicyVault: approve failed");

        (bool success, ) = protocol.call(data);
        require(success, "PolicyVault: execution failed");

        emit Executed(user, protocol, token, amount, planId);
    }

    function withdraw(address token, uint256 amount) external {
        require(balances[msg.sender][token] >= amount, "PolicyVault: insufficient balance");
        balances[msg.sender][token] -= amount;
        require(IERC20(token).transfer(msg.sender, amount), "PolicyVault: withdraw failed");
        emit Withdrawn(msg.sender, token, amount);
    }
}
