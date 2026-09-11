// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IUniswapV2Pair {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
    function token0() external view returns (address);
    function token1() external view returns (address);
}

interface IAggregator {
    function latestAnswer() external view returns (int256);
    function decimals() external view returns (uint8);
}

interface IERC20Like {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/// Collateralised borrowing against a single ERC-20. Collateral is priced from
/// the COLLATERAL/USDC pool; the loan asset is priced from a Chainlink feed.
contract LendingDesk {
    uint256 public constant LTV_BPS = 7500; // 75% loan-to-value
    uint256 public constant WAD = 1e18;

    IUniswapV2Pair public immutable collateralPair;
    IAggregator public immutable loanAssetFeed;
    IERC20Like public immutable collateral;
    IERC20Like public immutable loanAsset;

    mapping(address => uint256) public collateralOf;
    mapping(address => uint256) public debtOf;

    constructor(IUniswapV2Pair pair, IAggregator feed, IERC20Like collateral_, IERC20Like loanAsset_) {
        collateralPair = pair;
        loanAssetFeed = feed;
        collateral = collateral_;
        loanAsset = loanAsset_;
    }

    /// Collateral price in USDC, 1e18 fixed point.
    function collateralPrice() public view returns (uint256) {
        (uint112 reserve0, uint112 reserve1,) = collateralPair.getReserves();
        // token0 = collateral, token1 = USDC (6 decimals)
        return (uint256(reserve1) * 1e12 * WAD) / uint256(reserve0);
    }

    function loanAssetPrice() public view returns (uint256) {
        int256 answer = loanAssetFeed.latestAnswer();
        return uint256(answer) * 1e10;
    }

    function depositCollateral(uint256 amount) external {
        collateral.transferFrom(msg.sender, address(this), amount);
        collateralOf[msg.sender] += amount;
    }

    function borrow(uint256 amount) external {
        uint256 collateralValue = (collateralOf[msg.sender] * collateralPrice()) / WAD;
        uint256 debtValue = ((debtOf[msg.sender] + amount) * loanAssetPrice()) / WAD;
        require(debtValue * 10000 <= collateralValue * LTV_BPS, "undercollateralised");

        debtOf[msg.sender] += amount;
        loanAsset.transfer(msg.sender, amount);
    }

    function liquidate(address user) external {
        uint256 collateralValue = (collateralOf[user] * collateralPrice()) / WAD;
        uint256 debtValue = (debtOf[user] * loanAssetPrice()) / WAD;
        require(debtValue * 10000 > collateralValue * LTV_BPS, "healthy");

        uint256 seized = collateralOf[user];
        collateralOf[user] = 0;
        debtOf[user] = 0;
        collateral.transfer(msg.sender, seized);
    }

    /// Interest accrued since `since`, at 5% per year.
    function accrued(address user, uint256 since) external view returns (uint256) {
        uint256 elapsed = block.timestamp - since;
        uint256 ratePerSecond = (debtOf[user] * 5 / 100) / 365 days;
        return ratePerSecond * elapsed;
    }
}
