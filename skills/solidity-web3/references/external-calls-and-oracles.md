# External calls and oracles

Verified against: solc 0.8.37, Foundry 1.8.1, OpenZeppelin Contracts 5.7.0, Ethereum mainnet
fork at block 25953358.

## Contents

- [Low-level call semantics](#low-level-call-semantics)
- [Sending ETH](#sending-eth)
- [ERC-20 is a suggestion, not a standard](#erc-20-is-a-suggestion-not-a-standard)
- [SafeERC20 and balance deltas](#safeerc20-and-balance-deltas)
- [Approvals](#approvals)
- [Spot prices are attacker input](#spot-prices-are-attacker-input)
- [Chainlink-style feeds](#chainlink-style-feeds)
- [TWAPs](#twaps)
- [Flash loans change what "atomic" means](#flash-loans-change-what-atomic-means)
- [Untrusted contracts you call](#untrusted-contracts-you-call)
- [Reviewing an external dependency](#reviewing-an-external-dependency)

## Low-level call semantics

```solidity
(bool ok, bytes memory data) = target.call{value: amount}(payload);
if (!ok) revert CallFailed(data);
```

- **A failed `call` does not revert.** It returns `false`. An unchecked `call` is a silent
  failure that the rest of the function treats as success. `forge build` in 1.8.1 emits
  `unchecked-call` and `erc20-unchecked-transfer` lint notes for this. `[verified]`
- **A call to an address with no code succeeds** and returns empty data. So does a `staticcall`.
  A contract that "verified" a token by calling `decimals()` on a self-destructed address gets
  `ok == true` and zero bytes; decoding empty returndata as a `bool` or `uint256` is where
  `abi.decode` reverts, if you decode at all.
- **`delegatecall` runs the target's code against your storage.** A `delegatecall` to an
  attacker-chosen address is total compromise; a `delegatecall` to a library that
  `selfdestruct`s is a bricked contract. There is no safe `delegatecall` to an address a user
  supplies.
- **Return data is attacker-controlled memory.** A hostile callee can return megabytes to make
  your `returndatacopy` expensive (a gas bomb). Use `call` with a bounded decode, or the
  assembly form that ignores returndata, on paths where the caller pays.
- **The 63/64 rule (EIP-150).** A call forwards at most 63/64 of remaining gas, so the caller
  always keeps a 64th. An attacker can therefore make a sub-call run out of gas while the outer
  frame survives to observe the failure — which is why "the call failed so nothing happened" is
  not sound reasoning on a path with a `try/catch` or an unchecked `call`.

## Sending ETH

```solidity
(bool ok,) = recipient.call{value: amount}("");
if (!ok) revert TransferFailed();
```

Not `transfer`, not `send`. Both forward a 2300-gas stipend, which is not enough for a recipient
that writes one storage slot. The trace is unambiguous:

```
├─ [37759] Vault::payFees(1000000000000000000 [1e18])
│   ├─ [2300] HungryRecipient::receive{value: 1000000000000000000}()
│   │   └─ ← [OutOfGas] EvmError: OutOfGas
│   └─ ← [Revert] EvmError: Revert
```

`[verified]` The consequence is not theoretical: a fee recipient, a treasury, a Safe, or any
contract with an accounting `receive()` cannot be paid by `transfer`. Gas costs also change at
hard forks, so a hard-coded stipend is a future breakage even for recipients that fit today.

Using `call` re-opens reentrancy, which is the trade you are making: pair it with CEI ordering
and a guard. For distributions, prefer pull over push so one recipient cannot block the rest.

## ERC-20 is a suggestion, not a standard

Assume every token in the system is one of these until proven otherwise:

| Behaviour | Examples | What breaks |
|---|---|---|
| Returns no `bool` | USDT, BNB, OMG | `IERC20.transfer` reverts on decoding, or the ABI-decoder accepts garbage |
| Returns `false` instead of reverting | ZRX, EURS | an unchecked call credits a transfer that never happened |
| Fee on transfer | STA, PAXG, some wrapped assets | received amount < requested amount; crediting the argument over-credits |
| Rebasing / balance changes without a transfer | stETH, AMPL | cached balances drift; `totalAssets` moves with no event |
| Blocklists | USDC, USDT | a pull or push to a blocked address reverts forever, bricking a queue |
| Pausable | BNB, ZIL | the same, temporarily |
| Low or high decimals | USDC 6, Gemini USD 2, WBTC 8 | hard-coded 1e18 scaling |
| Reverts on zero-value transfer | LEND | a legitimate zero-amount path reverts |
| Reverts on large approvals | UNI, COMP (`uint96` allowance) | `approve(type(uint256).max)` reverts |
| `transferFrom` with `src == msg.sender` behaves like `transfer` | some | allowance accounting differs |
| Non-string metadata | MKR (`bytes32 name`) | a UI or a wrapper that decodes `string` reverts |
| Hooks on transfer | ERC-777 | reentrancy from what looks like a plain token move |
| Multiple addresses for one token | some bridged assets | a per-token allowlist keyed by address is bypassable |
| Upgradeable | USDC, USDT | today's behaviour is not a guarantee |

Write down which of these the protocol tolerates. "We only support standard tokens" is a valid
decision, and then it needs an allowlist rather than a comment.

## SafeERC20 and balance deltas

```solidity
import {SafeERC20, IERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
using SafeERC20 for IERC20;

uint256 before = token.balanceOf(address(this));
token.safeTransferFrom(msg.sender, address(this), amount);
uint256 received = token.balanceOf(address(this)) - before;   // not `amount`
credit[msg.sender] += received;
```

`SafeERC20` handles the missing-return-value and false-return cases; it does **not** handle
fee-on-transfer or rebasing. Measuring the delta does. Use the measured amount in every
subsequent line of accounting.

One `SafeERC20` trap: `safeTransfer` on an address with no code succeeds, because empty
returndata passes the `success && (data.length == 0 || decoded)` check. A sentinel address used
to mean "native ETH" (`address(0)`, `0xEeee…eEEeE`) therefore silently no-ops instead of
reverting. Branch on the sentinel explicitly.

## Approvals

- Never leave a residual allowance: approve exactly what the call needs, and zero it afterwards
  if the callee might not spend it all.
- `increaseAllowance` and `decreaseAllowance` were removed from OpenZeppelin's `ERC20` in 5.0.
  Use `SafeERC20.forceApprove` (which handles tokens that require a zero-first reset) or
  `safeIncreaseAllowance`. `safeApprove` was also removed. `[verified]`
- `permit` (EIP-2612) is not universal, and DAI's variant has a different signature. A `permit`
  call wrapped in `try/catch` so that failure is ignored turns a griefable approval into a
  silent one.
- The approval front-running race (spend the old allowance, then the new one) is inherent to
  `approve`; the mitigation is approving zero first or using `permit` with a nonce, not
  recommending the removed `increaseAllowance`.

## Spot prices are attacker input

```solidity
function collateralPrice() public view returns (uint256) {
    (uint112 r0, uint112 r1,) = pair.getReserves();
    return (uint256(r1) * 1e12 * WAD) / uint256(r0);   // manipulable
}
```

Measured on the fixture: changing the pool's reserves within one transaction moved the reported
price from `2000e18` to `80e18` — a 25x move — and inflating it the other way let a position
worth $20k borrow $300k. `[verified]` Any of `getReserves()`, `slot0()`, `balanceOf` of a pool,
or `getAmountsOut` is a single-block quantity that a flash loan can set to almost any value.

The rule: a price used for solvency, liquidation or minting decisions never comes from a
single instantaneous read of a pool you do not control. Acceptable sources, in order:

1. A push oracle with multiple independent reporters (a Chainlink-style aggregator), with
   freshness and deviation checks.
2. A TWAP over a window long enough that moving it costs more than the attack yields.
3. Two of the above, with a maximum-divergence check that pauses on disagreement.

An LP-token or vault-share price derived from `totalAssets / totalSupply` where `totalAssets`
reads `balanceOf(address(this))` is the same bug in a different shape: a donation moves it.

## Chainlink-style feeds

```solidity
(, int256 answer,, uint256 updatedAt,) = feed.latestRoundData();
if (answer <= 0) revert BadPrice(answer);
if (block.timestamp - updatedAt > MAX_AGE) revert StalePrice(updatedAt);
uint256 price = uint256(answer) * 10 ** (18 - feed.decimals());
```

Measured against the mainnet ETH/USD aggregator on a fork: `description "ETH / USD"`,
`decimals 8`, `answer 247209000000`, `updatedAt` 948 seconds before the fork's block timestamp.
Warping the fork 30 days forward returned **the same answer with the same `updatedAt`** — the
call itself gives no indication that the data is a month old. `[verified]`

Therefore:

- `latestAnswer()` returns only the number and cannot be checked for freshness. It still exists
  on the aggregator (verified on the fork) which is why it keeps appearing in new code; use
  `latestRoundData()`. `[verified]`
- `MAX_AGE` comes from the feed's own heartbeat and deviation threshold, per feed and per chain.
  A single global `MAX_AGE` constant for feeds with different heartbeats produces either
  spurious reverts or no protection.
- Check `answer > 0` before the cast. A negative `int256` cast to `uint256` becomes ~1.15e77.
- On an L2, also check the sequencer-uptime feed: while the sequencer is down, prices freeze and
  liquidations computed from them are wrong in whoever's favour the freeze happened to land.
- A feed can be paused, deprecated, or hit a min/max circuit-breaker answer; during the LUNA
  collapse feeds reported their floor. Decide what the protocol does when the price is at a
  circuit-breaker bound, and write it down.
- `answeredInRound < roundId` was the old staleness signal on aggregator proxies; treat the
  `updatedAt` age bound as the primary check and keep the code readable.

## TWAPs

A TWAP is manipulation-*resistant*, not manipulation-proof: the cost of moving it scales with
the window. Practical notes:

- The window must be longer than one block, and long enough that the capital cost of holding a
  skewed price for that long exceeds the extractable profit. Single-block "TWAPs" (two
  observations from the same block) are spot prices with extra steps.
- Uniswap V3's tick-cumulative oracle needs the pool to have enough observation slots; a pool
  with a short observation array cannot serve a long window, and a freshly created pool cannot
  serve any.
- Liquidity matters more than the window. A TWAP on a thin pool is cheap to move for the whole
  window.
- Cache and clamp: bound how far the price is allowed to move between reads, and pause if it
  exceeds the bound.

## Flash loans change what "atomic" means

Assume the attacker starts each transaction with unlimited capital that must be repaid by the
end of it. That invalidates three common assumptions:

- "Nobody can hold enough tokens to move the price" — they can, for one transaction.
- "The attacker cannot be the largest LP / voter / staker" — they can, for one transaction.
- "These two steps happen in different blocks" — they do not have to.

The defences are structural: price from something a single transaction cannot move, snapshot
governance weight at a past block, and require a minimum holding period before a deposit earns
anything. Checking `msg.sender == tx.origin` is not a defence — it is obsolete under EIP-7702
and hostile to smart accounts.

## Untrusted contracts you call

For every external address the contract stores or accepts, answer: who sets it, can it be
changed after deployment, what happens if it reverts, what happens if it returns garbage, and
what happens if it calls back. Then:

- Wrap optional calls in `try/catch` with a bounded fallback, and make sure the `catch` branch
  does not silently skip an accounting step.
- Treat `staticcall` as the default for reads, so a "view" dependency cannot write your state.
- For a hook or adapter address, keep an allowlist the owner maintains rather than accepting any
  address from the caller — and remember that the allowlist's owner is now part of the trust
  model.

## Reviewing an external dependency

- [ ] List every external address: tokens, pools, feeds, routers, hooks, adapters, registries.
- [ ] For each, record who sets it and whether it is mutable.
- [ ] For each token, mark which of the non-standard behaviours above the protocol tolerates.
- [ ] For each value read, ask what a flash loan can make that value be within one transaction.
- [ ] For each price, check: source, freshness bound, positivity, decimals conversion, and what
      happens when it is unavailable.
- [ ] For each call, check the return value, the empty-code case, and the reentrancy window.
- [ ] Write fork tests against the real dependency — a mock proves your assumption, not the
      chain's behaviour.
- [ ] **Gate — every price path has an age bound and a positivity check proven by a fork test,
      every token transfer is measured rather than assumed, and every stored external address
      has a named setter.**

<!-- sources: pashov-auditor, pashov-xray, tob-secure-contracts, oz-contracts, max-taylor-sol, layerghost-kit, foundry-book -->
