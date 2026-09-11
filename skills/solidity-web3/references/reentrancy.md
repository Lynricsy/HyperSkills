# Reentrancy

Verified against: solc 0.8.37, Foundry 1.8.1, OpenZeppelin Contracts 5.7.0, Slither 0.11.6.

## Contents

- [The four shapes](#the-four-shapes)
- [Single-function: the drain](#single-function-the-drain)
- [The checked-arithmetic variant is a different bug](#the-checked-arithmetic-variant-is-a-different-bug)
- [Cross-function](#cross-function)
- [Cross-contract](#cross-contract)
- [Read-only reentrancy](#read-only-reentrancy)
- [Where the callbacks are](#where-the-callbacks-are)
- [Guards](#guards)
- [Modifier order](#modifier-order)
- [What Slither does and does not tell you](#what-slither-does-and-does-not-tell-you)
- [Reviewing for it](#reviewing-for-it)

## The four shapes

| Shape | Re-entered function | Who loses | Guard that closes it |
|---|---|---|---|
| Single-function | the same function | the contract | `nonReentrant` on it, or CEI ordering |
| Cross-function | a *different* state-changing function sharing the state | the contract | `nonReentrant` on **every** function touching that state |
| Cross-contract | a sibling contract sharing state or a registry | the system | a shared guard, or state updated before any call out |
| Read-only | a `view` an integrator reads | the *integrating* protocol | the view respecting the same guard, or effects before interactions |

Only the first is what most reviews check. The last is the one that reaches production, because
a `view` function looks harmless and the loss lands on someone else's balance sheet.

## Single-function: the drain

```solidity
function withdrawAll() external {
    uint256 amount = balanceOf[msg.sender];
    require(amount > 0, "nothing to withdraw");

    (bool ok,) = msg.sender.call{value: amount}("");   // interaction first
    require(ok, "transfer failed");

    balanceOf[msg.sender] = 0;                          // effect after
    totalDeposits -= amount;
}
```

The attacker is one contract:

```solidity
contract Drainer {
    Vault public vault;
    function attack() external payable {
        vault.deposit{value: msg.value}();
        vault.withdrawAll();
    }
    receive() external payable {
        if (address(vault).balance >= 1 ether) vault.withdrawAll();
    }
}
```

Measured on the fixture (`evals/files/Vault.sol`), depositing 1 ETH into a vault holding 10:

```
vault balance before 10000000000000000000
vault balance after  0
drainer balance      12000000000000000000
reentrant hits       10
```

`[verified]` The recursion terminates on the attacker's own condition, not on anything the vault
does. The fix is to move the two state writes above the call; adding a gas limit to the call
does not work, because the attacker only needs one `CALL` worth of gas per level.

## The checked-arithmetic variant is a different bug

The same ordering mistake with a partial-withdraw signature behaves differently:

```solidity
function withdraw(uint256 amount) external {
    require(balanceOf[msg.sender] >= amount, "insufficient balance");
    (bool ok,) = msg.sender.call{value: amount}("");
    require(ok, "transfer failed");
    balanceOf[msg.sender] -= amount;      // subtract, not zero
    totalDeposits -= amount;
}
```

The inner frame subtracts first, so the outer frame's `-=` underflows and 0.8.x reverts. The
whole transaction unwinds, the attacker gets nothing, and the honest user's own withdrawal
reverts with `transfer failed` if anything in their receive path re-enters. `[verified]`

Report this as a denial-of-service and a latent drain (one refactor away), not as an
exploitable theft — and never report it as "safe because Solidity 0.8". The distinction matters
in a review because the remediation urgency differs, and because claiming a drain you cannot
reproduce costs the reader's trust in the findings that are real.

## Cross-function

Guarding only the function that calls out is not enough when two functions share state:

```solidity
function withdrawAll() external nonReentrant { /* calls out, then zeroes */ }
function transfer(address to, uint256 amount) external {   // unguarded
    balanceOf[msg.sender] -= amount;
    balanceOf[to] += amount;
}
```

From the callback, the attacker calls `transfer` instead of `withdrawAll`: the balance has not
been zeroed yet, so it moves the still-credited amount to a second address and then collects it
normally. Slither reports this explicitly — it lists the functions the shared variable "can be
used in cross function reentrancies" in, which on the fixture was `deposit`, `receive`,
`shareOf`, `withdraw` and `withdrawAll`. `[verified]`

The rule: `nonReentrant` belongs on every externally reachable function that touches the state
the guarded function is mid-way through updating, not only on the one that makes the call.

## Cross-contract

Two contracts of the same system sharing a registry, an accounting contract, or a price cache
each hold their own `ReentrancyGuard`, and a per-contract guard does nothing about a callback
that enters the *other* one. This is the form that survives an audit of each contract in
isolation. Look for it wherever contract A writes state that contract B reads, and B is callable
in the window between A's external call and A's write.

## Read-only reentrancy

```solidity
function shareOf(address user) external view returns (uint256) {
    if (totalDeposits == 0) return 0;
    return (balanceOf[user] * 1e18) / totalDeposits;
}
```

Measured during the callback, with the reader holding 5 ETH of a 15 ETH vault:

```
share quoted outside callback 333333333333333333
share quoted inside callback  333333333333333333
totalDeposits inside callback 15000000000000000000
vault ETH inside callback     10000000000000000000
```

`[verified]` The share is unchanged, and that is the bug: the vault has already paid out 5 ETH
but still claims 15 ETH of deposits, so anything that values a share as
`totalAssets / totalShares` — or that reads `totalDeposits` as TVL — reads a number inflated by
50% for the duration of the callback. A lending market accepting these shares as collateral
issues a loan against value that has left.

You cannot fix this in the integrator. Fix it at the source: update accounting before calling
out, or make the view revert while the guard is held. OpenZeppelin's `ReentrancyGuard` exposes
`_reentrancyGuardEntered()` for exactly this:

```solidity
function shareOf(address user) external view returns (uint256) {
    if (_reentrancyGuardEntered()) revert ReentrancyGuardReentrantCall();
    // ...
}
```

When reviewing an integration, the question is not "is this view guarded" but "what does this
view divide by, and can a callback make the numerator and denominator disagree".

## Where the callbacks are

Every one of these hands control to untrusted code:

- `call`, `delegatecall`, `staticcall` (a `staticcall` cannot write, but the callee can still
  read your mid-update state and call a third contract's writes)
- `transfer`, `send` (2300 gas is enough to read state and call a cheap view)
- ERC-721 `safeTransferFrom` → `onERC721Received` on the recipient
- ERC-1155 `safeTransferFrom`/`safeBatchTransferFrom` → `onERC1155Received`
- ERC-777 `tokensToSend`/`tokensReceived` hooks — an ERC-20-shaped token that calls you back
- Fee-on-transfer and rebasing tokens with hooks in `_update`
- ERC-4626 vaults whose underlying token has hooks
- Any "reward hook", "strategy", "adapter" or "callback receiver" address the contract stores
- Oracle and router callbacks (`uniswapV3SwapCallback`, flash-loan `executeOperation`)

A guard on the ETH path and nothing on the hook path is the most common half-fix. On the fixture
vault, `rewardHook.onWithdraw` is reached *before* any state change, so it re-enters exactly as
`receive()` does. `[verified]`

## Guards

```solidity
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ReentrancyGuardTransient} from "@openzeppelin/contracts/utils/ReentrancyGuardTransient.sol";
```

The path is `utils/`, not `security/` — `contracts/security/` was removed in OpenZeppelin 5.0,
and an import from it fails to resolve rather than compiling. `[verified]` The revert is the
custom error `ReentrancyGuardReentrantCall()`, not the 4.x string `"ReentrancyGuard: reentrant
call"`, so any test asserting that string passes vacuously or fails. `[verified]`

| | `ReentrancyGuard` | `ReentrancyGuardTransient` |
|---|---|---|
| Storage | one persistent slot | transient (EIP-1153) |
| Requires | any 0.8.x | `evm_version` ≥ cancun, and solc ≥ 0.8.34 in practice |
| Cost | cold `SSTORE` on first use per tx | `TSTORE`/`TLOAD`, no refund games |

Prefer the transient variant on chains that have EIP-1153, but only on solc ≥ 0.8.34: the
`TransientStorageClearingHelperCollision` bug (introduced 0.8.28, fixed 0.8.34, high severity)
can leave storage or transient storage uncleared when a contract clears both, which is exactly
the guard's own operation. `[verified]`

Neither guard supports a `nonReentrant` function calling another `nonReentrant` function of the
same contract — the second call reverts. Split the work into an external guarded wrapper and an
internal unguarded implementation.

## Modifier order

Modifiers execute left to right. `function f() external nonReentrant whenNotPaused` runs the
guard first; `function f() external onlyRoleWithCallback nonReentrant` runs whatever that first
modifier does — including any external call it makes to check a registry — outside the guard.
Put `nonReentrant` first and keep external calls out of modifiers.

## What Slither does and does not tell you

On the fixture set, `slither . --exclude-dependencies` reported:

- `reentrancy-eth` on both `withdraw` and `withdrawAll`, with the cross-function variable list —
  the real finding, correctly identified. `[verified]`
- `reentrancy-benign` and `reentrancy-events` on the same functions for the `totalDeposits` write
  and the trailing `emit`. These are the *same* bug reported again at lower severity; do not
  report them as separate findings.
- Nothing at all about the read-only reentrancy through `shareOf`. There is no detector for
  "an integrator prices collateral from this view". `[verified]`

## Reviewing for it

- [ ] List every external call, hook and token transfer in the contract, with its line.
- [ ] For each, list the state that is *not yet* consistent at that point.
- [ ] For each piece of that state, list every externally reachable function — including views —
      that reads or writes it.
- [ ] Any pair (call site, reachable function) with no shared guard is a candidate. Write the
      two-transaction sequence; if you can, write the attacker contract and prove it.
- [ ] Check the guard's own coverage: does it cover the hook path as well as the ETH path, is it
      first in the modifier list, and is the view path covered.
- [ ] **Gate — a reentrancy finding ships with a Foundry test containing an attacker contract
      whose `receive()` re-enters, asserting the attacker's ending balance exceeds its deposit
      (or, for the read-only case, asserting the view's value inside the callback).**

<!-- sources: pashov-auditor, tob-secure-contracts, oz-contracts, wshobson-solsec, layerghost-kit, slither -->
