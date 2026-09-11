// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IRewardHook {
    function onWithdraw(address user, uint256 amount) external;
}

/// Deposit vault with a pluggable reward hook. Shares are quoted to a lending
/// market through `shareOf`, which other protocols read to price collateral.
contract Vault {
    address public owner;
    address public feeRecipient;
    uint16 public feeBps;
    IRewardHook public rewardHook;

    mapping(address => uint256) public balanceOf;
    uint256 public totalDeposits;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    constructor() {
        owner = msg.sender;
        feeRecipient = msg.sender;
        feeBps = 50;
    }

    function deposit() external payable {
        require(msg.value > 0, "zero deposit");
        balanceOf[msg.sender] += msg.value;
        totalDeposits += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    function withdrawAll() external {
        uint256 amount = balanceOf[msg.sender];
        require(amount > 0, "nothing to withdraw");

        if (address(rewardHook) != address(0)) {
            rewardHook.onWithdraw(msg.sender, amount);
        }

        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");

        balanceOf[msg.sender] = 0;
        totalDeposits -= amount;
        emit Withdrawn(msg.sender, amount);
    }

    function withdraw(uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "insufficient balance");

        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");

        balanceOf[msg.sender] -= amount;
        totalDeposits -= amount;
        emit Withdrawn(msg.sender, amount);
    }

    /// Share of the vault owned by `user`, in 1e18 fixed point.
    function shareOf(address user) external view returns (uint256) {
        if (totalDeposits == 0) return 0;
        return (balanceOf[user] * 1e18) / totalDeposits;
    }

    function setFeeRecipient(address recipient) external {
        feeRecipient = recipient;
    }

    function setFeeBps(uint16 bps) external {
        require(tx.origin == owner, "not owner");
        feeBps = bps;
    }

    function setRewardHook(IRewardHook hook) external {
        require(tx.origin == owner, "not owner");
        rewardHook = hook;
    }

    function payFees(uint256 amount) external {
        require(msg.sender == owner, "not owner");
        payable(feeRecipient).transfer(amount);
    }

    function distribute(address[] calldata users, uint256 amountEach) external {
        require(msg.sender == owner, "not owner");
        for (uint256 i = 0; i < users.length; i++) {
            payable(users[i]).transfer(amountEach);
        }
    }

    receive() external payable {
        balanceOf[msg.sender] += msg.value;
        totalDeposits += msg.value;
    }
}
