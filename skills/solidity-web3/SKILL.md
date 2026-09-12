---
name: solidity-web3
description: "Develops and audits Solidity smart contracts with Foundry security testing."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

Paths below are relative to this skill's directory.

## Scope

Defensive work on EVM contracts you own or are being paid to review: writing them, reviewing
them for the failure classes that lose funds, upgrading them behind a proxy, and proving both
with Foundry. Verified against Solidity 0.8.37, OpenZeppelin Contracts 5.7.0, Foundry 1.8.1
and Slither 0.11.6.

Contract-specific vulnerability classes — reentrancy in all four shapes, oracle manipulation,
proxy storage collisions, precision and rounding, non-standard ERC-20 behaviour, gas griefing —
and the Foundry and Slither toolchain that demonstrates them are this skill's job. General
application security-audit methodology — threat modelling, coverage ledgers, severity
derivation, false-positive governance, report structure — is the `security-review` skill's;
bring a finding's severity and the report shape from there and the contract reasoning from here.

This skill is defensive only. It exists to make your own contracts survive, and to find the bugs
in them before someone else does. Reproduction happens locally: a Foundry test, a fork of public
state, a local `anvil`. Broadcasting a transaction against a contract you do not control,
extracting value from other users' transactions, and anything intended to evade monitoring are
out of scope; asked for those, say so and stop. A finding that only mainnet can settle is
reported as a validation blocker with the read-only check its owner can run.

Not covered, with where it belongs: the dApp front-end, wagmi/viem hooks and wallet connection
belong to the `react` skill; TypeScript and its tooling to `typescript`; indexers and off-chain
services to `nodejs-backend`; wallet and exchange product APIs are out of scope entirely. Chains
that are not EVM-and-Solidity — Solana, Cairo, Move, CosmWasm — have no skill in this library
yet; say so rather than improvising one. Deployment infrastructure, key custody hardware and
CI runners belong to `containers`, `github` and the cloud skills.

## Core rules

1. **Pin the compiler in `foundry.toml`.** On a fresh machine Foundry 1.8.1 selected solc 0.8.36
   for `pragma ^0.8.24` while 0.8.37 was already released, then switched to 0.8.37 once that
   version was present locally. Unpinned, your CI and your laptop produce different bytecode from
   the same source. `[verified]`
2. **Use 0.8.34+ if any contract or dependency touches transient storage.**
   `TransientStorageClearingHelperCollision` (high severity, introduced 0.8.28, fixed 0.8.34) can
   leave one of storage or transient storage uncleared — which silently disarms a transient
   reentrancy guard. 0.8.37 is the first release with an empty known-bug list. `[verified]`
3. **Order every state-changing function checks, effects, interactions.** With the external call
   before the balance write, a re-entering recipient drained a fixture vault from 10 ETH to 0 in
   one transaction. `[verified]`
4. **A `-=` after the external call is not a safer version of the same bug.** Checked arithmetic
   turns the second pass into an underflow revert, so the same ordering mistake reads as
   "transfer failed" and denies the honest user instead of paying the attacker (0.8.x). Report it
   as an availability defect, not as a drain. `[verified]`
5. **Every callback is an entry point, not just the ETH transfer.** A reward hook, an
   `onERC721Received`, an ERC-777 `tokensReceived` or a fee-on-transfer token reached before the
   state write re-enters exactly like `receive()` does.
6. **View functions need the same guard as the writes they mirror.** Mid-callback, a fixture
   vault's accounting still reported 15 ETH of deposits while it held 10, so any protocol pricing
   collateral from that view read a 50%-inflated number. Read-only reentrancy costs the
   *integrating* protocol, which is why it survives review. `[verified]`
7. **`nonReentrant` comes first in the modifier list.** Modifiers run left to right; a guard
   behind a modifier that itself makes an external call is not protecting that call.
8. **Authorize on `msg.sender`, never `tx.origin`.** `tx.origin == owner` is satisfied by any
   contract the owner is merely interacting with; a relay contract flipped a fixture's fee to 100%
   this way. It also breaks under EIP-7702 delegated accounts and every smart-contract wallet.
   `[verified]`
9. **Enumerate privileged functions and name the role for each.** A function with no check is a
   finding whether or not it looks harmless: an unguarded `setFeeRecipient` redirects the fee
   stream, and static analysis reported only a missing zero-address check on it. `[verified]`
10. **Send ETH with `call` and check the return value.** `transfer`/`send` forward 2300 gas; the
    trace shows `receive{value: …}()` entered with `[2300]` and returning `OutOfGas`, so any
    contract recipient that writes one storage slot cannot be paid. `[verified]`
11. **Pay out by pull, not by push loop.** One recipient that reverts — or that consumes the whole
    gas budget — bricks a `for` loop over users for everyone behind it.
12. **Treat every ERC-20 as hostile: `SafeERC20`, and measure balances.** Missing return values,
    fee-on-transfer, rebasing, blocklists and 6- or 24-decimal tokens each break a contract that
    assumes `transferFrom(amount)` moved exactly `amount`.
13. **Multiply before dividing, and divide once.** A fixture that precomputed a per-second rate as
    `(debt * 5 / 100) / 365 days` under-charged a 6-decimal position by 37% over a year.
    `[verified]`
14. **Explicit narrowing casts truncate silently in 0.8.x.** `uint128(2**128 + 7)` returns `7`
    with no revert; only `SafeCast` reverts. Do not record a bare cast as safe because the
    compiler is 0.8. `[verified]`
15. **Never take a price from a single spot read of an AMM pool.** Changing a fixture pool's
    reserves in one transaction moved its reported price from 2000 to 80, and a 25x inflation let
    a $20k position borrow $300k. Use a manipulation-resistant feed, or a TWAP over a window
    longer than one block. `[verified]`
16. **Every oracle read is bounded by age and sanity.** `latestRoundData()` with an `updatedAt`
    freshness bound and a positive-answer check, not `latestAnswer()`: warping a fork 30 days
    past the last update returned the same answer with the same `updatedAt`, and nothing in the
    call signals staleness. `[verified]`
17. **Upgrades append storage; they never insert or reorder.** Prepending two variables to a
    fixture's V2 made slot 1 (`totalStaked`, 7 ether) read as `treasury`
    `0x…6124feE993BC0000`, and V2's `totalStaked` read V1's `cooldown` (604800). Verify with
    `forge inspect <contract> storage-layout` on both versions before deploying. `[verified]`
18. **`_authorizeUpgrade` must be gated, and an empty override is a live vulnerability.** With the
    body empty, an arbitrary address called `upgradeToAndCall` on the fixture proxy and replaced
    the implementation. `[verified]`
19. **Call `_disableInitializers()` in every implementation constructor.** Otherwise anyone
    initializes the implementation itself and becomes its owner — which matters the moment the
    implementation has a `delegatecall` or a `selfdestruct` path. `[verified]`
20. **Constructor and `immutable` state does not exist for proxy users.** A V2 constructor that
    set `rewardRate = 100` read back as `57005` through the proxy — the old `stakingToken`
    address in slot 0. Initialize in an initializer. `[verified]`
21. **Post-upgrade initialization uses `reinitializer(n)`.** `initializer` on an already
    initialized proxy reverts `InvalidInitialization()` (OpenZeppelin 5.x). `[verified]`
22. **Check OpenZeppelin 5.x shapes against the installed source, not memory.**
    `Ownable(initialOwner)` is mandatory (omitting it is compiler error 3415), `contracts/security/`
    no longer exists, `Counters`/`increaseAllowance`/`safeApprove`/`upgradeTo` are gone, and
    reverts are custom errors — `OwnableUnauthorizedAccount(address)`,
    `ERC20InsufficientBalance(address,uint256,uint256)`, `ReentrancyGuardReentrantCall()` — so
    every test asserting `"Ownable: caller is not the owner"` is testing nothing. `[verified]`
23. **An invariant run is only evidence if the calls landed.** `[invariant] fail_on_revert`
    defaults to `false` (the `[fuzz]` one defaults to `true`), and a handler whose every call
    reverted printed `payFees 42678 calls / 42678 reverts` under a green `[PASS]`. Read the
    per-selector table every time. `[verified]`
24. **Assert the specific revert.** Bare `vm.expectRevert()` passes on any revert, including the
    access-control error that fires before the logic under test. Pass the selector or the reason.
    `[verified]`
25. **A finding ships with a Foundry test that fails before the fix and passes after.** Slither
    found the `reentrancy-eth` and the `divide-before-multiply` in the fixtures but reported
    nothing about the missing owner check, the oracle, or the empty `_authorizeUpgrade`; a
    detector hit is a lead, and a passing PoC is a finding.

## Workflows

### implement

- [ ] Read `foundry.toml` and the installed dependency source before writing anything: compiler
      version, remappings, optimizer, and the actual OpenZeppelin major version in `lib/`.
- [ ] Write the storage layout and the privileged-function inventory first, then the logic.
      Name the role that guards each entry point, or mark it permissionless deliberately.
- [ ] Apply the baseline in `references/solidity-baseline.md`: custom errors, explicit
      visibility, immutable where possible, events on every state transition, CEI ordering.
- [ ] Keep value flows pull-based, use `SafeERC20`, and measure balance deltas rather than
      trusting arguments.
- [ ] Write the tests with the code, not after: one unit test per branch, a fuzz test for every
      arithmetic boundary, and an invariant for each conservation property.
- [ ] **Gate — `forge build` clean (including `forge lint` notes triaged), `forge fmt --check`
      clean, `forge test` green, and every `[invariant]` run shows non-reverting calls in its
      per-selector table.**

### review

A contract, a pull request, or a whole `src/` tree you own.

- [ ] Establish what holds value and what must always be true about it. Write the invariants
      down before reading for bugs; they are what tells a quirk from a vulnerability.
- [ ] Inventory entry points: external and public functions, `receive`/`fallback`, callbacks the
      contract exposes to tokens and hooks, and everything reachable by `delegatecall`.
- [ ] Run the tools first because they are cheap: `forge build`, `slither . --exclude-dependencies`,
      and `slither-check-upgradeability` if there is a proxy. Triage every hit against
      `references/static-analysis-and-audit-checklist.md` before reading further.
- [ ] Walk the classes in order of realised losses, using the topic references: reentrancy
      (all four shapes), access control and initialization, proxy and storage, arithmetic and
      rounding, external calls and token assumptions, oracles, gas and DoS.
- [ ] For each candidate, write the attack as a sequence of transactions with a named actor. If
      you cannot, it is a lead, not a finding.
- [ ] Reproduce each finding as a Foundry test and record the command and output.
- [ ] **Gate — every finding has `file:line`, an actor, a reproducing test, and a fix; every
      dismissed detector hit has a reason; classes you did not examine are listed by name.**

### upgrade

- [ ] Confirm the proxy pattern from on-chain state, not from the repository: read slot
      `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` (ERC-1967
      implementation) and the admin slot, and identify UUPS versus Transparent versus Beacon.
- [ ] Diff `forge inspect <old> storage-layout` against `forge inspect <new> storage-layout` and
      require an append-only change; run `slither-check-upgradeability`.
- [ ] Check the initialization story: `_disableInitializers()` in the new constructor,
      `reinitializer(n)` for new state, and no constructor or `immutable` assignment that proxy
      users are expected to see.
- [ ] Check the authorization story: `_authorizeUpgrade` gated by owner, role or timelock, and
      who actually holds that key today.
- [ ] Fork mainnet at a recent block, upgrade the real proxy in the fork, and re-read user
      balances and the protocol's own invariants through the proxy.
- [ ] **Gate — storage diff is append-only, the fork upgrade preserves every user balance and
      invariant, and the upgrade authority is a multisig or timelock rather than an EOA.**

### test

- [ ] Read the existing suite for what it cannot fail: a green suite with no attacker contract
      says nothing about reentrancy, and a `vm.expectRevert()` with no argument says nothing
      about which revert happened.
- [ ] Add the adversarial unit tests: an attacker contract per callback surface, an expected
      revert with its selector per guard, and a boundary test per cast and per division.
- [ ] Add fuzz tests with `bound` rather than `vm.assume` for ranges, so runs are not thrown
      away by rejection.
- [ ] Add a handler-based invariant suite per `references/invariant-and-fuzz-testing.md`: ghost
      variables for what the contract does not track, actors, and donation paths.
- [ ] Add fork tests for every external dependency: token, oracle, pool, and the proxy itself.
- [ ] Measure instead of claiming: `forge coverage` per branch, and read the invariant
      per-selector table.
- [ ] **Gate — each new test fails against the unfixed code (show it), the invariant suite
      reports non-reverting calls, and coverage is reported per branch rather than as one
      percentage.**

## Topic router

| Topic | Read when | File |
|---|---|---|
| Compiler version policy and the known-bug list, contract layout, custom errors, events, `receive`/`fallback`, storage and data location traps, `unchecked` | Writing or reviewing any contract, or choosing a pragma | `references/solidity-baseline.md` |
| Single-function, cross-function, cross-contract and read-only reentrancy, callback surfaces, `ReentrancyGuard` versus `ReentrancyGuardTransient`, modifier order, the checked-arithmetic variant | Any function that calls out, or any view an integrator reads | `references/reentrancy.md` |
| Ownable/Ownable2Step/AccessControl in 5.x, role layering, timelocks, two-step transfers, signature authorization, `ecrecover`, replay and EIP-712 | Auditing permissions, or adding a privileged function | `references/access-control.md` |
| ERC-1967 slots, UUPS versus Transparent versus Beacon, storage layout rules and ERC-7201 namespaces, initializers, upgrade authorization, verification tooling | Anything behind a proxy, or planning an upgrade | `references/proxy-upgrades.md` |
| Checked arithmetic, `unchecked`, silent cast truncation, `SafeCast`, operation order, decimals, rounding direction, share inflation | Reading any formula that moves value | `references/arithmetic-and-precision.md` |
| Low-level call semantics, `SafeERC20`, non-standard token behaviours, sending ETH, spot-price manipulation, Chainlink freshness, TWAPs, flash-loan atomicity | The contract calls a token, a pool or a price feed | `references/external-calls-and-oracles.md` |
| Unbounded loops, push versus pull, the 2300-gas stipend, the 63/64 rule, block gas limit, contract size limit, storage cost and transient storage | Reviewing loops, payouts or anything an attacker can make expensive | `references/gas-and-dos.md` |
| Project config, test naming, cheatcodes, precise revert assertions, fuzzing with `bound`, fork tests, coverage, `forge lint` and `forge fmt`, CI | Writing or fixing Foundry tests | `references/foundry-testing.md` |
| Handler-based invariant suites, `targetContract`/`targetSelector`, ghost variables, `fail_on_revert` semantics, reading the calls/reverts table, shrinking and replay, invariants by protocol type | Proving a conservation property, or when a suite passes suspiciously | `references/invariant-and-fuzz-testing.md` |
| Slither invocation and detector triage, the measured false-positive classes, `slither-check-upgradeability`, what static analysis cannot find, the review checklist and deliverables | Triaging tool output, or producing a review write-up | `references/static-analysis-and-audit-checklist.md` |

## Output format

One Markdown write-up. Order findings by severity, skip empty sections, and state what you did
not examine. Severity derivation and the wider report contract belong to the `security-review`
skill; what follows is the contract-specific evidence each finding must carry.

```markdown
# Contract review — <scope> @ <commit>

**Built with** solc <version>, Foundry <version>, OpenZeppelin <version>.
**Method** Source review; local Foundry reproduction; fork of <chain> at block <n>.
No transaction was broadcast to any network.

## Findings
### <n>. <title> — <severity>
- **Location** `src/File.sol:123`
- **Actor** <who, holding what, with what starting capital>
- **Sequence** <tx 1 → tx 2 → …, or "single transaction" with the flash-loan step named>
- **Invariant broken** <the property, and the value before and after>
- **Proof** `forge test --match-test test_<name> -vvv` → <the assertion that fires>
- **Fix** <the change> — **Regression test** <what fails before it>

## Leads (no reproduction yet)
| Location | Suspicion | What would settle it |

## Dismissed detector hits
| Tool | Detector | Location | Why it is not a finding |

## Not examined
- <class or file, and why>
```

## Environment

- Foundry: `curl -L https://foundry.paradigm.xyz | bash && foundryup`. Claims here were measured
  against forge 1.8.1 and solc 0.8.36/0.8.37. Pin `solc` in `foundry.toml`.
- OpenZeppelin: `forge install OpenZeppelin/openzeppelin-contracts@v5.7.0` (and
  `openzeppelin-contracts-upgradeable@v5.7.0` for proxies), with both remapped — in 5.x the
  upgradeable package's `Initializable.sol` and `UUPSUpgradeable.sol` are re-export shims that
  need the core remapping to resolve.
- Slither: `uv tool install slither-analyzer` (measured against 0.11.6, 102 detectors). It
  drives `forge build` itself, so run it from the project root.
- Fork tests need an RPC endpoint in `[rpc_endpoints]`; without one, say that the fork-dependent
  claims were not checked rather than implying they were.
- Never put a private key in a file, a command line, an environment variable or a test fixture.
  Use `forge script --account <keystore-name> --sender <address>`, and keep deployment keys in a
  hardware wallet or a keystore. Admin roles belong to a multisig from the first deployment.
