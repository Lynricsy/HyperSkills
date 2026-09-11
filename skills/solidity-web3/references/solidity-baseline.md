# Solidity baseline

Verified against: solc 0.8.37, Foundry 1.8.1, OpenZeppelin Contracts 5.7.0.

## Contents

- [Compiler version policy](#compiler-version-policy)
- [The known-bug list is a document you can read](#the-known-bug-list-is-a-document-you-can-read)
- [Pragma discipline](#pragma-discipline)
- [File and contract layout](#file-and-contract-layout)
- [Errors](#errors)
- [Events](#events)
- [Data location](#data-location)
- [Constant, immutable and the proxy exception](#constant-immutable-and-the-proxy-exception)
- [receive, fallback and the ETH entry points](#receive-fallback-and-the-eth-entry-points)
- [unchecked](#unchecked)
- [Checks, effects, interactions](#checks-effects-interactions)
- [Deletion and struct copies](#deletion-and-struct-copies)

## Compiler version policy

Foundry picks the compiler for you unless you tell it not to. On a clean machine, forge 1.8.1
(built 2026-08-28) compiled `pragma solidity ^0.8.24;` with **solc 0.8.36** — downloading it on
demand — although 0.8.37 had already been released. After `forge build --use 0.8.37` fetched
0.8.37, a `forge clean && forge build --force` then selected 0.8.37. The version that produced
your bytecode is therefore a property of the machine, not of the repository. `[verified]`

Pin it:

```toml
[profile.default]
solc = "0.8.37"
evm_version = "cancun"   # or "prague"; whatever the target chain actually runs
optimizer = true
optimizer_runs = 200
```

`evm_version` matters as much as `solc`. Transient storage (`tstore`/`tload`, EIP-1153) and
therefore `ReentrancyGuardTransient` require Cancun or later, and a chain that has not forked
yet will reject the bytecode. `MCOPY` and `SELFDESTRUCT` semantics also changed at Cancun.

## The known-bug list is a document you can read

The Solidity repository publishes machine-readable bug data: `docs/bugs.json` (one entry per
bug, with `introduced`, `fixed`, `severity`) and `docs/bugs_by_version.json` (the bug names open
in each release). Read it instead of guessing whether a version is safe. As of 0.8.37:

| Bug | Severity | Introduced | Fixed | Why it matters |
|---|---|---|---|---|
| `TransientStorageClearingHelperCollision` | high | 0.8.28 | 0.8.34 | Clearing storage and transient storage in the same contract may clear only one. A transient reentrancy guard can be left set or unset unexpectedly. |
| `InheritanceOrderReversalOnStorageEndWarning` | medium | 0.8.29 | 0.8.36 | Emitting one warning reversed `linearizedBaseContracts`, so inheritance resolved in the wrong order. Miscompilation, not a warning. |
| `UnsoundSpillInMutualRecursion` | medium | 0.7.2 | 0.8.36 | Locals of mutually recursive functions could be spilled to fixed memory offsets and overwritten. |
| `SpillSlotCollisionAcrossMutualRecursion` | low/medium | 0.7.2 | 0.8.37 | Two simultaneously live functions could receive the same spill offset. |
| `MemoryByteArrayElementDeleteClearsWholeWord` | low/medium | — | 0.8.37 | `delete` on one element of a memory `bytes` zeroes up to 31 bytes past it. |
| `MisorderedNamedParametersInRequireWithCustomErrors` | very low | 0.8.26 | 0.8.37 | Named-parameter custom-error arguments in `require` were encoded in call-site order under via-IR. |

0.8.37 is the first release whose `bugs_by_version` entry is empty. `[verified]`

Practical floor: **0.8.34** if anything in the tree uses transient storage, **0.8.36** if any
contract has mutual recursion or deep inheritance, **0.8.37** otherwise — and whatever you pick,
pin it and state it in the README.

## Pragma discipline

- Contracts that get deployed: exact pragma (`pragma solidity 0.8.37;`). The deployed bytecode
  should be reproducible from the repository alone.
- Interfaces and libraries meant to be imported by others: a range (`^0.8.24`), because a
  narrower pragma forces your consumers to your compiler.
- Tests and scripts: a range is fine; they are never deployed.

A floating pragma on a deployed contract means the source you verified on a block explorer and
the source you reviewed can be different compilations.

## File and contract layout

One contract per file, named after the file. Inside a contract, a fixed order makes review
mechanical because a reader knows where to look for the storage layout:

1. `type` declarations, `using` directives
2. Constants and immutables
3. Storage variables, in declaration order (this *is* the storage layout)
4. Events
5. Errors
6. Modifiers
7. `constructor`
8. `receive`, `fallback`
9. External, public, internal, private functions, `view`/`pure` last within each group

Two consequences that are not cosmetic. Storage variable order is a deployment-visible ABI for
proxies, so it needs to be visible in one screen. And a
layout convention makes a diff that inserts a variable in the middle of the storage block
obvious to a human reviewer.

## Errors

Custom errors, not revert strings:

```solidity
error Unauthorized(address caller);
error InsufficientBalance(uint256 requested, uint256 available);

if (msg.sender != owner) revert Unauthorized(msg.sender);
require(amount <= balance, InsufficientBalance(amount, balance)); // 0.8.26+
```

Reasons beyond calldata size: an error carries the values a reviewer needs, tests can assert the
selector plus the arguments, and a `string` reason cannot be matched precisely by callers. From
0.8.26 `require` accepts a custom error directly; before that only `revert` did. `forge build`
emits a `custom-errors` lint note on every string `require`. `[verified]`

Do not use the named-parameter form inside `require` on solc < 0.8.37 — the arguments were
ABI-encoded in the wrong order under via-IR (see the bug table).

## Events

Emit on every state transition that an off-chain consumer or an incident responder would need to
reconstruct: balance changes, role changes, parameter changes, upgrades, pauses. Index the
fields that get filtered (`address` participants, ids), leave amounts unindexed.

The failure this prevents is not gas: it is being unable to answer "when did this parameter
change, and to what" after an incident. Emit *after* the state change and *before* the external
call where possible; an event emitted after an external call can be observed in a reentrant
frame in the wrong order, which is what Slither's `reentrancy-events` detector reports.

## Data location

- `calldata` for read-only reference-type parameters of external functions. `memory` copies the
  whole array; `calldata` does not.
- `memory` when you need to mutate a copy.
- `storage` pointers are aliases, not copies: `Item storage item = items[id];` followed by
  `delete items[id]` leaves `item` pointing at the cleared slot, and writes through it resurrect
  fields. Take the pointer after any deletion, never before.
- A `struct` in `storage` assigned from `memory` copies field by field; a nested mapping inside
  that struct is not copied and keeps whatever it had.

## Constant, immutable and the proxy exception

`constant` is inlined at every use; `immutable` is written into the deployed bytecode by the
constructor. Both remove an `SLOAD`, and both are invisible through a proxy: constructor code
runs against the implementation's own storage and bytecode, so a proxy delegating to that
implementation reads whatever the proxy's storage happens to hold. A fixture that set
`rewardRate = 100` in a V2 constructor read back `57005` through the proxy — the old
`stakingToken` address sitting in slot 0. `[verified]`

Rule: no `constructor` state and no `immutable` in a contract that will sit behind a proxy,
except for values that are genuinely per-implementation (and mark them
`@custom:oz-upgrades-unsafe-allow state-variable-immutable` so the plugin agrees).

## receive, fallback and the ETH entry points

A contract with neither `receive` nor a payable `fallback` rejects plain ETH transfers. If you
add one, remember it is a state-changing entry point reachable by anyone, including from inside
a reentrant frame:

```solidity
receive() external payable {
    balanceOf[msg.sender] += msg.value;   // an entry point, with all that implies
    totalDeposits += msg.value;
}
```

Two traps. A `receive` that writes storage costs more than the 2300 gas a `transfer`/`send`
forwards, so any counterparty paying you with `transfer` cannot.
And a `fallback` that silently accepts unmatched selectors turns a caller's typo — or a removed
function in a later version — into a successful no-op call.

## unchecked

`unchecked { }` is correct where the bound is proved by surrounding code and the gas matters:

```solidity
for (uint256 i = 0; i < items.length;) {
    // ...
    unchecked { ++i; }   // i < items.length <= 2**64 by array bounds
}
```

It is wrong wherever the bound comes from an argument. Inside `unchecked`, 0.8's revert-on-
overflow is gone and the semantics are pre-0.8 wraparound. When reviewing, treat each
`unchecked` block as a claim that needs a one-line proof next to it; if the claim is not written
down, that is the finding.

## Checks, effects, interactions

The ordering rule that prevents the largest class of losses:

```solidity
function withdrawAll() external {
    uint256 amount = balanceOf[msg.sender];
    require(amount > 0, NothingToWithdraw());   // checks

    balanceOf[msg.sender] = 0;                  // effects
    totalDeposits -= amount;

    (bool ok,) = msg.sender.call{value: amount}("");   // interactions
    if (!ok) revert TransferFailed();
}
```

Inverting the last two lines let a fixture attacker take 10 ETH out of a vault it had deposited
1 ETH into, in a single transaction. `[verified]` The detailed taxonomy — including the variant
where checked arithmetic converts the drain into a denial of service, and the read-only case
that costs an integrating protocol instead of you — is in the reentrancy topic.

## Deletion and struct copies

`delete arr[i]` on a dynamic array zeroes the element and leaves the length unchanged, so the
array keeps a zero hole; `arr[i] = arr[arr.length - 1]; arr.pop();` is the swap-and-pop that
actually removes it, at the cost of reordering. `delete` on a struct containing a mapping clears
only the non-mapping fields — the mapping's entries survive, and a later struct reused at the
same index inherits them. Both patterns show up in registries and vesting schedules, where the
resurrected field is an allowance or a claimed flag.

<!-- sources: solidity-docs, foundry-book, oz-contracts, cyfrin-solskill, layerghost-kit -->
