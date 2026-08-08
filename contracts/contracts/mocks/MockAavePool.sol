// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20Min {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/// @notice Mimics the real Aave V3 Pool.supply() signature and pull-based
/// transfer semantics, so contract tests exercise the exact calldata shape
/// AgentVault's backend builds for the real Base Sepolia Aave Pool
/// (0xA238Dd80C259a72e81d7e4664a9801593F98d1c5).
contract MockAavePool {
    // user => asset => supplied amount (stands in for aTokens)
    mapping(address => mapping(address => uint256)) public supplied;

    event Supply(address indexed asset, address indexed onBehalfOf, uint256 amount, uint16 referralCode);

    function supply(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external {
        require(
            IERC20Min(asset).transferFrom(msg.sender, address(this), amount),
            "MockAavePool: transferFrom failed"
        );
        supplied[onBehalfOf][asset] += amount;
        emit Supply(asset, onBehalfOf, amount, referralCode);
    }
}
