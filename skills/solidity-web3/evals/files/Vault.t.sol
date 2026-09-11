// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Vault} from "../src/Vault.sol";

contract VaultTest is Test {
    Vault internal vault;
    address internal alice = address(0xA11CE);
    address internal bob = address(0xB0B);

    function setUp() public {
        vault = new Vault();
        vm.deal(alice, 10 ether);
        vm.deal(bob, 10 ether);
    }

    function test_Deposit() public {
        vm.prank(alice);
        vault.deposit{value: 1 ether}();
        assertEq(vault.balanceOf(alice), 1 ether);
        assertEq(vault.totalDeposits(), 1 ether);
    }

    function test_WithdrawAll() public {
        vm.prank(alice);
        vault.deposit{value: 2 ether}();

        vm.prank(alice);
        vault.withdrawAll();

        assertEq(vault.balanceOf(alice), 0);
        assertEq(alice.balance, 10 ether);
    }

    function test_PartialWithdraw() public {
        vm.prank(alice);
        vault.deposit{value: 3 ether}();

        vm.prank(alice);
        vault.withdraw(1 ether);

        assertEq(vault.balanceOf(alice), 2 ether);
    }

    function test_ShareOf() public {
        vm.prank(alice);
        vault.deposit{value: 1 ether}();
        vm.prank(bob);
        vault.deposit{value: 3 ether}();

        assertEq(vault.shareOf(alice), 0.25e18);
        assertEq(vault.shareOf(bob), 0.75e18);
    }

    function test_SetFeeBps() public {
        vault.setFeeBps(100);
        assertEq(vault.feeBps(), 100);
    }

    function test_WithdrawRevertsWhenEmpty() public {
        vm.prank(alice);
        vm.expectRevert();
        vault.withdrawAll();
    }
}
