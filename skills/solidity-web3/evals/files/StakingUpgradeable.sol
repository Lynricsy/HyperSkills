// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Initializable} from "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import {UUPSUpgradeable} from "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import {OwnableUpgradeable} from "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// V1, already deployed behind an ERC-1967 proxy and holding user funds.
contract StakingV1 is Initializable, OwnableUpgradeable, UUPSUpgradeable {
    IERC20 public stakingToken;
    uint256 public totalStaked;
    mapping(address => uint256) public stakedOf;
    uint256 public cooldown;

    function initialize(IERC20 token, address owner_) external initializer {
        __Ownable_init(owner_);
        stakingToken = token;
        cooldown = 7 days;
    }

    function stake(uint256 amount) external {
        stakingToken.transferFrom(msg.sender, address(this), amount);
        stakedOf[msg.sender] += amount;
        totalStaked += amount;
    }

    function unstake(uint256 amount) external {
        require(stakedOf[msg.sender] >= amount, "insufficient stake");
        stakedOf[msg.sender] -= amount;
        totalStaked -= amount;
        stakingToken.transfer(msg.sender, amount);
    }

    function _authorizeUpgrade(address newImplementation) internal override {}
}

/// V2 adds a reward rate and a treasury. Deploy target of the next upgrade.
contract StakingV2 is Initializable, OwnableUpgradeable, UUPSUpgradeable {
    uint256 public rewardRate;
    address public treasury;
    IERC20 public stakingToken;
    uint256 public totalStaked;
    mapping(address => uint256) public stakedOf;
    uint256 public cooldown;

    constructor() {
        rewardRate = 100;
    }

    function initializeV2(uint256 rate, address treasury_) external initializer {
        rewardRate = rate;
        treasury = treasury_;
    }

    function stake(uint256 amount) external {
        stakingToken.transferFrom(msg.sender, address(this), amount);
        stakedOf[msg.sender] += amount;
        totalStaked += amount;
    }

    function unstake(uint256 amount) external {
        require(stakedOf[msg.sender] >= amount, "insufficient stake");
        stakedOf[msg.sender] -= amount;
        totalStaked -= amount;
        stakingToken.transfer(msg.sender, amount);
    }

    function pendingReward(address user) external view returns (uint256) {
        return (stakedOf[user] * rewardRate) / 10000;
    }

    function sweepToTreasury(uint256 amount) external onlyOwner {
        stakingToken.transfer(treasury, amount);
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}
