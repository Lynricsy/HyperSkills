// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {AccessManaged} from "@openzeppelin/contracts/access/manager/AccessManaged.sol";
import {AccessManager} from "@openzeppelin/contracts/access/manager/AccessManager.sol";
import {Multicall} from "@openzeppelin/contracts/utils/Multicall.sol";

/// Collects protocol fees and forwards them to the treasury.
/// Every privileged entry point is gated by the protocol's AccessManager.
contract FeeRouter is AccessManaged, Multicall {
    IERC20 public immutable asset;
    address public treasury;
    uint16 public feeBps;

    event Harvested(uint256 amount);

    constructor(address manager, IERC20 asset_, address treasury_) AccessManaged(manager) {
        asset = asset_;
        treasury = treasury_;
        feeBps = 50;
    }

    function harvest() external restricted {
        uint256 amount = asset.balanceOf(address(this)) * feeBps / 10_000;
        asset.transfer(treasury, amount);
        emit Harvested(amount);
    }

    function setFeeBps(uint16 bps) external restricted {
        feeBps = bps;
    }

    function setTreasury(address treasury_) external restricted {
        treasury = treasury_;
    }

    function sweep(IERC20 token, address to) external restricted {
        token.transfer(to, token.balanceOf(address(this)));
    }
}

/// Called once right after deployment; it is granted ADMIN_ROLE on the manager for that call
/// only, and the admin multisig revokes it in the same batch.
contract ConfigureFeeRouter {
    uint64 public constant KEEPER_ROLE = 1; // off-chain bot, hot key on the harvesting server
    uint64 public constant PARAM_ROLE = 2;  // governance multisig

    function configure(AccessManager manager, FeeRouter router, address bot, address governance) external {
        // The bot harvests and may batch several harvests in one transaction.
        bytes4[] memory keeperSelectors = new bytes4[](2);
        keeperSelectors[0] = FeeRouter.harvest.selector;
        keeperSelectors[1] = Multicall.multicall.selector;
        manager.setTargetFunctionRole(address(router), keeperSelectors, KEEPER_ROLE);

        bytes4[] memory paramSelectors = new bytes4[](3);
        paramSelectors[0] = FeeRouter.setFeeBps.selector;
        paramSelectors[1] = FeeRouter.setTreasury.selector;
        paramSelectors[2] = FeeRouter.sweep.selector;
        manager.setTargetFunctionRole(address(router), paramSelectors, PARAM_ROLE);

        manager.grantRole(KEEPER_ROLE, bot, 0);
        manager.grantRole(PARAM_ROLE, governance, 2 days); // every parameter change waits two days
        manager.setTargetAdminDelay(address(router), 3 days); // authority changes wait three days
    }
}
