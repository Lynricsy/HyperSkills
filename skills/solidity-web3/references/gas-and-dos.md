# Gas and denial of service

Verified against: solc 0.8.37, Foundry 1.8.1.

## Contents

- [Availability is a security property](#availability-is-a-security-property)
- [Unbounded loops](#unbounded-loops)
- [Push payments give every recipient a veto](#push-payments-give-every-recipient-a-veto)
- [The 2300-gas stipend](#the-2300-gas-stipend)
- [Griefing with gas](#griefing-with-gas)
- [Storage that only grows](#storage-that-only-grows)
- [The 24 KB code-size limit](#the-24-kb-code-size-limit)
- [Gas optimisations that are actually correctness changes](#gas-optimisations-that-are-actually-correctness-changes)
- [Optimisations worth making](#optimisations-worth-making)
- [Measuring instead of guessing](#measuring-instead-of-guessing)
- [Reviewing for it](#reviewing-for-it)

## Availability is a security property

A contract that cannot execute a liquidation, a withdrawal or a pause is losing money just as
surely as one being drained — and the attacker's cost is usually a fraction of the damage.
Every "this loop is a bit expensive" comment is really the question *can an attacker make this
function impossible to call*.

Three ingredients turn a gas observation into a finding: an attacker-controlled growth vector,
a function that must remain callable, and no alternative path. State all three or it is a gas
note, not a vulnerability.

## Unbounded loops

```solidity
function distribute(address[] calldata users, uint256 amountEach) external onlyOwner {
    for (uint256 i = 0; i < users.length; i++) {
        payable(users[i]).transfer(amountEach);   // external call in a loop
    }
}
```

Two separate problems: the loop is unbounded in length, and it makes an external call per
iteration. `forge build` flags the second directly as a `calls-loop` lint, and Slither reports
it as `calls-loop`. `[verified]`

The dangerous variant is a loop over storage the *attacker* can extend — a holders array, a
queue, a per-user positions list. If adding an entry is cheap and iterating costs gas per
entry, an attacker adds entries until the function exceeds the block gas limit, permanently.
Look for:

- `for` over a storage array whose `push` is reachable without a check
- an inner call that itself loops (`O(n·m)`)
- a "process all pending" function with no cursor
- `delete` of a large array or mapping-of-structs in one call

Fixes: paginate with an explicit cursor (`process(uint256 from, uint256 to)`), cap the array at
a hard constant, or invert the flow so each user pays for their own iteration.

## Push payments give every recipient a veto

In the loop above, any single recipient that reverts — because it has no `receive`, because its
`receive` costs more than the stipend, because a token blocklist hit, or because it deliberately
reverts — takes the whole distribution down, for everyone. This is the classic "king of the
hill" bug: the current beneficiary refuses the refund, so nobody can replace them.

Pull is the default:

```solidity
mapping(address => uint256) public claimable;

function allocate(address user, uint256 amount) internal { claimable[user] += amount; }

function claim() external {
    uint256 amount = claimable[msg.sender];
    claimable[msg.sender] = 0;                       // effects
    (bool ok,) = msg.sender.call{value: amount}(""); // interaction
    if (!ok) revert TransferFailed();
}
```

Each recipient's failure is now local to them, and the protocol keeps working. Where a push is
genuinely required (an auction refund), push with a bounded `call` and fall back to crediting
`claimable` when it fails — never let the failure revert the whole transaction.

## The 2300-gas stipend

`transfer` and `send` forward 2300 gas, which permits a couple of `SLOAD`s and an event but not
an `SSTORE` to a cold slot. Measured trace of a payment to a recipient whose `receive()`
increments a counter:

```
├─ [2300] HungryRecipient::receive{value: 1e18}()
│   └─ ← [OutOfGas] EvmError: OutOfGas
```

`[verified]` Do not "fix" this by raising the stipend — use `call` with the full gas and a
reentrancy guard. Conversely, when *your* contract has a `receive()` that writes storage, be
aware that every counterparty paying with `transfer` cannot pay you; a minimal `receive() external
payable {}` is sometimes the right design, with the accounting done by an explicit `deposit()`.

## Griefing with gas

Beyond the block limit, three shapes recur:

- **Return-data bombs.** A callee returns a huge `bytes`, and the caller pays for
  `returndatacopy`. Use the assembly `call` form that ignores returndata, or bound the copy, on
  paths where a third party chooses the callee.
- **Memory expansion.** Memory cost is quadratic beyond 724 words; an attacker-supplied array
  length can make a function cost far more than its logic suggests. Validate lengths before
  allocating.
- **The 63/64 rule.** A sub-call receives at most 63/64 of remaining gas, so an attacker can
  arrange for an inner call to run out of gas while the outer frame continues. Any `try/catch`
  or unchecked `call` whose failure path skips accounting is exploitable this way: the attacker
  chooses *which* step fails.

## Storage that only grows

A mapping is cheap to write and impossible to enumerate; an array is enumerable and therefore a
liability. Anything append-only that a permissionless function extends is an attack surface —
and `delete` does not reclaim it: zeroing a slot refunds at most a fraction of the write.

Prefer: a mapping plus an off-chain index built from events; a linked list with O(1) removal; a
fixed-size ring buffer. Where an array is unavoidable, make removal swap-and-pop and document
that order is not stable.

## The 24 KB code-size limit

EIP-170 caps deployed bytecode at 24576 bytes. `forge build --sizes` prints the size and margin
per contract; a contract that compiles locally with the optimizer on and fails to deploy on a
chain with different settings is a release-day surprise. Check the margin in CI rather than at
deployment time. `[official]`

When a contract is too large: split it, move logic into `internal` libraries (inlined) or
`external` libraries (`delegatecall`ed, which changes the trust model), replace revert strings
with custom errors, and remove dead code paths. Turning the optimizer to a high `runs` value
trades deployment size for runtime cost — measure both.

## Gas optimisations that are actually correctness changes

Treat these as code changes needing tests, not as free wins:

| "Optimisation" | What it really changes |
|---|---|
| `unchecked { }` | removes overflow protection; needs a written bound proof |
| Packing to `uint96`/`uint112` | introduces a silent ceiling and a truncating cast |
| Caching a storage value across an external call | the cache is stale if the callee re-enters |
| Removing an event | removes the only record an incident responder has |
| Removing a zero-address check | lets funds go to a burn address |
| `payable` on a function that should not receive ETH | adds an ETH-accepting path with no accounting |
| Replacing `call` with `transfer` to save gas | reintroduces the stipend failure |
| Skipping a `require` because "the caller always checks" | the caller is not always yours |

## Optimisations worth making

Safe, measurable, and they do not change behaviour:

- `calldata` instead of `memory` for external read-only reference parameters.
- `immutable`/`constant` for values fixed at deployment — never in a contract behind a proxy,
  where constructor and bytecode state is invisible to proxy users.
- Cache a repeated `storage` read in a local, within a block that makes no external call.
- Do not initialise to the type's default (`uint256 i = 0` writes nothing but costs bytes).
- Short-circuit the cheap check first in a compound condition, and revert as early as possible.
- Pack struct fields that are genuinely bounded — with `SafeCast` at the assignment.
- Custom errors instead of revert strings (smaller bytecode and smaller calldata on revert).
- Do not cache `arr.length` for a `calldata` array; reading it is a single cheap opcode.

## Measuring instead of guessing

```bash
forge test --gas-report                  # per-function min/avg/median/max
forge build --sizes                      # deployed size and margin vs the 24 KB limit
forge snapshot                           # write .gas-snapshot
forge snapshot --check                   # fail CI on a regression
forge test --match-test test_X -vvvv     # per-call gas in the trace
```

The trace is the authoritative number: it shows the gas actually forwarded to each sub-call,
which is how the 2300-gas failure above was identified rather than inferred. Gas assertions of
the form `assertLt(gasUsed, 50_000)` are brittle — a cold `SSTORE` alone is 20 000 — so snapshot
diffs are the better regression tool.

## Reviewing for it

- [ ] List every loop and, for each, who controls the iteration count.
- [ ] List every external call inside a loop; each is a per-iteration veto.
- [ ] For every payout, decide push or pull and check the failure is local to one recipient.
- [ ] Find every `transfer`/`send` of ETH and check the recipient can be a contract.
- [ ] Check `try/catch` and unchecked-call failure branches for skipped accounting.
- [ ] Check array growth: is `push` permissionless, and is there a cap or a cursor.
- [ ] Run `forge build --sizes` and record the margin for every deployed contract.
- [ ] **Gate — every availability finding names the growth vector, the function that stops
      working and the absence of an alternative path; gas claims come from `--gas-report` or a
      trace rather than from reasoning.**

<!-- sources: pashov-auditor, tob-secure-contracts, cyfrin-solskill, foundry-book, tenequm-foundry -->
