# Invariant and fuzz campaigns

Verified against: forge 1.8.1, solc 0.8.37.

## Contents

- [What an invariant is](#what-an-invariant-is)
- [The handler pattern](#the-handler-pattern)
- [Targeting](#targeting)
- [fail_on_revert, and the run that proves nothing](#fail_on_revert-and-the-run-that-proves-nothing)
- [Reading a real failure](#reading-a-real-failure)
- [Ghost variables](#ghost-variables)
- [Actors and donations](#actors-and-donations)
- [Budgets and reproducibility](#budgets-and-reproducibility)
- [Invariants by protocol type](#invariants-by-protocol-type)
- [Properties that are not properties](#properties-that-are-not-properties)
- [When to reach for Echidna or Medusa instead](#when-to-reach-for-echidna-or-medusa-instead)
- [Building a suite](#building-a-suite)

## What an invariant is

A statement about the system's state that must hold after **every** sequence of permitted
calls, by any caller, in any order. Not "the function returns the right value" — that is a unit
test — but "the contract always holds at least what it claims to owe".

The invariant is the thing that tells a quirk from a vulnerability. Write the invariants before
hunting for bugs; a finding is a demonstrated invariant break, and a suspicion with no broken
invariant is a lead.

Good invariants share a shape: they compare two independently computed quantities (accounting
versus reality, sum of parts versus recorded total, a round trip versus its input) so that a bug
in one side is not mirrored in the other.

## The handler pattern

The fuzzer calling the contract directly wastes almost every run on reverts and cannot express
"a user who already deposited". A handler sits between them, bounding inputs and choosing
actors:

```solidity
contract VaultHandler is Test {
    Vault public vault;
    address[3] public actors = [address(0xA1), address(0xA2), address(0xA3)];
    uint256 public ghostDeposited;
    uint256 public ghostWithdrawn;

    constructor() {
        vault = new Vault();
        for (uint256 i = 0; i < actors.length; i++) vm.deal(actors[i], 100 ether);
    }

    function deposit(uint256 actorSeed, uint256 amount) external {
        address actor = actors[actorSeed % actors.length];
        amount = bound(amount, 1, 10 ether);
        vm.deal(actor, amount);
        vm.prank(actor);
        vault.deposit{value: amount}();
        ghostDeposited += amount;
    }

    function withdraw(uint256 actorSeed, uint256 amount) external {
        address actor = actors[actorSeed % actors.length];
        uint256 balance = vault.balanceOf(actor);
        if (balance == 0) return;                 // skip, do not revert
        amount = bound(amount, 1, balance);
        vm.prank(actor);
        vault.withdraw(amount);
        ghostWithdrawn += amount;
    }
}

contract VaultInvariantTest is Test {
    VaultHandler internal handler;
    Vault internal vault;

    function setUp() public {
        handler = new VaultHandler();
        vault = handler.vault();
        targetContract(address(handler));
    }

    function invariant_SolvencyBacksAccounting() public view {
        assertGe(address(vault).balance, vault.totalDeposits());
    }

    function invariant_AccountingMatchesGhosts() public view {
        assertEq(vault.totalDeposits(), handler.ghostDeposited() - handler.ghostWithdrawn());
    }
}
```

Three rules the handler must follow: bound every input rather than rejecting it, return early
instead of reverting when a precondition fails, and mirror every state change into a ghost
variable so the invariant has something independent to compare against.

## Targeting

- `targetContract(address)` — restrict the fuzzer to the handler. Without it, the engine targets
  every contract deployed in `setUp`, including the vault itself, and most calls revert.
- `targetSelector(FuzzSelector({addr: h, selectors: sels}))` — restrict to specific functions,
  which is how you keep a helper or a view out of the campaign.
- `excludeContract(address)` / `excludeSender(address)` — keep mocks and privileged addresses
  out.
- `targetSender(address)` — the fuzzer otherwise invents senders; with a handler that `prank`s
  internally, the sender the engine picks is irrelevant and appears in the counterexample as
  noise.

## fail_on_revert, and the run that proves nothing

`[invariant] fail_on_revert` defaults to **`false`**, while `[fuzz] fail_on_revert` defaults to
**`true`**. `[official]` The consequence is the single most common way an invariant suite lies:

```
VaultInvariantTest invariants:
[PASS] invariant_AccountingMatchesGhosts
[PASS] invariant_SolvencyBacksAccounting
 VaultInvariantTest invariants (runs: 256, calls: 128000, reverts: 42678)

| Contract     | Selector | Calls | Reverts | Discards |
| VaultHandler | deposit  | 42732 | 0       | 0        |
| VaultHandler | payFees  | 42678 | 42678   | 0        |   <-- never executed once
| VaultHandler | withdraw | 42590 | 0       | 0        |
```

Every single `payFees` call reverted — the handler was paying a fee recipient that could not
accept ETH — and the suite still reported `[PASS]`. `[verified]` The invariant was never
evaluated after the only state transition that could break it.

So: read the per-selector table on every run. A selector at or near 100% reverts is a broken
handler, not a safe contract. Run with `fail_on_revert = true` while developing the handler to
surface the reverts, then relax it only for selectors whose reverts are genuinely expected.

`Discards` counts calls the engine threw away (for example a `bound` that rejected); a high
discard count means the handler is filtering too hard.

## Reading a real failure

With the handler fixed so `payFees` executes, the same suite breaks immediately:

```
{"timestamp":…,"event":"failure","invariant":"invariant_SolvencyBacksAccounting",
 "reason":"assertion failed: 844264577245486604 < 844264577245486654"}

[FAIL: assertion failed: 844264577245486604 < 844264577245486654] invariant_SolvencyBacksAccounting
        [Sequence] (original: 7, shrunk: 2)
                sender=0x…A1 addr=[…:VaultHandler] calldata=deposit(uint256,uint256) args=[0, 6.654e38]
                sender=0x…4d9 addr=[…:VaultHandler] calldata=payFees(uint256) args=[50]

 VaultInvariantTest invariants (runs: 256, calls: 128000, reverts: 9563)
Fuzz seed: 0x42437f2d…
```

`[verified]` What to take from it:

- `(original: 7, shrunk: 2)` — the engine minimised a 7-call sequence to the 2 calls that
  matter. Read the shrunk sequence; it is the PoC.
- The counterexample is 50 wei of fees. Magnitude is irrelevant to correctness, and a shrunk
  counterexample is usually at a boundary.
- `reverts: 9563` out of 128000 is healthy — those are the `withdraw` calls that hit an empty
  balance.
- `Fuzz seed:` makes the run reproducible: `forge test --fuzz-seed 0x4243…`.
- Convert the shrunk sequence into a named unit test. The invariant suite finds it once; the
  unit test keeps it found.

## Ghost variables

Track in the handler what the contract does not track itself:

- Running sums of inputs and outputs (`ghostDeposited`, `ghostWithdrawn`) — the independent side
  of a conservation invariant.
- The set of actors that ever interacted, so an invariant can iterate real users rather than
  arbitrary addresses.
- The maximum value a quantity ever reached, for monotonicity invariants.
- A count of how many times each branch was taken, to prove the campaign reached the branch at
  all — a cheap substitute for coverage in an invariant run.

A ghost variable that merely mirrors a storage slot is worthless: if the handler computes it the
same way the contract does, both are wrong together.

## Actors and donations

Two things the fuzzer will not do unless the handler lets it:

- **Multiple actors.** One actor cannot break an invariant that depends on users interfering
  with each other. Three is usually enough; pick by `seed % actors.length` so the engine can
  steer.
- **Donations.** Send ETH or tokens to the contract *without* going through its entry points, to
  break any accounting that reads `balanceOf(address(this))` or `address(this).balance`. If a
  donation breaks an invariant, that is the share-inflation and price-manipulation class showing
  up in a test instead of in production.

Also include the adversarial paths: a `receive()` that re-enters, a token that takes a fee, a
recipient that reverts. A handler with only well-behaved participants tests a world that does
not exist.

## Budgets and reproducibility

Defaults: `[invariant] runs = 256`, `depth = 500` — so 128 000 calls per invariant group, which
matches the `calls: 128000` in the output above. `[official]` `shrink_run_limit` bounds the
minimisation effort (0 disables shrinking).

```toml
[profile.default.invariant]
runs = 256
depth = 500
fail_on_revert = true

[profile.deep.invariant]
runs = 5_000
depth = 1_000
```

Keep the default profile fast enough to run on every commit and a deep profile for nightly.
Record the seed of any failure in the regression test's comment.

## Invariants by protocol type

Start from this list, then derive the ones specific to the protocol's own accounting:

| Protocol | Invariants worth asserting |
|---|---|
| Any vault or pool | `balance(token) >= sum(credited)`; `totalSupply == sum(balanceOf)`; a donation cannot increase any user's claim |
| ERC-4626 | `convertToAssets(convertToShares(x)) <= x`; `maxWithdraw` is actually withdrawable; deposit-then-redeem never returns more than deposited |
| Lending | every position is either healthy or liquidatable, never neither; `sum(debt) == totalBorrows`; a liquidation never increases the borrower's health debt-free |
| AMM | `k` never decreases except by the fee; a swap round trip returns less than it took; reserves match balances |
| Staking / rewards | `sum(pendingReward) <= rewardBalance`; unstaking never returns more than staked plus accrued |
| Perps | sum of PnL across positions is zero (plus fees); the insurance fund never goes negative |
| Governance | voting power is snapshotted, so a flash loan cannot vote; a proposal cannot execute before its delay |
| Access control | no sequence of unprivileged calls changes an owner-only piece of state |
| Anything with a counter | monotonic where claimed, and never wraps |

The strongest invariants are round trips and conservation sums, because they compare the
contract against arithmetic rather than against itself.

## Properties that are not properties

- **Tautologies.** `assertEq(add(a, b), a + b)` restates the implementation;
  `assertGe(someUint, 0)` is compiler-guaranteed; `assertGe(address(this).balance, 0)` likewise.
- **Vacuous runs.** A handler that returns early on almost every input, or an `assume` that
  rejects almost every input, produces a green suite that executed nothing. The per-selector
  table and the discard count are how you notice.
- **Invariants that depend on call order** are not invariants; they are unit tests.
- **Invariants asserted on the handler's own state** test the handler.
- Code with no algebraic structure gets example-based tests, and saying so is a valid outcome —
  padding an invariant suite with restatements of the code is worse than not having one.

## When to reach for Echidna or Medusa instead

Foundry's invariant engine is in-repo, needs no extra toolchain, and runs in CI — make it the
default. Reach for the Trail of Bits fuzzers when the campaign is the point rather than the
regression:

- **Echidna** — mature property fuzzer; `echidna_`-prefixed properties must be `view`/`pure`
  with no arguments (a property that mutates state changes what it is testing), plus an
  assertion mode for properties about a specific operation. `[official]`
- **Medusa** — parallel and coverage-guided, faster on large suites; same methodology.
- **crytic/properties** publishes ready-made property sets (ERC-20, ERC-721, ERC-4626, fixed-point
  math) with harness scaffolding. It is AGPL-3.0: read it for the property *names* and the
  harness shape, and do not vendor its `.sol` files into a project you distribute. `[official]`

Both take long-running campaigns with a corpus; both are a poor fit for a pull-request gate. A
reasonable split: Foundry invariants on every commit, a nightly Echidna or Medusa campaign, and
every counterexample either fuzzer finds converted into a Foundry unit test.

## Building a suite

- [ ] Write the invariants in English first, each comparing two independently computed
      quantities.
- [ ] Write the handler: bounded inputs, early returns, ghost variables, several actors,
      donation paths, and at least one adversarial participant.
- [ ] `targetContract` the handler; exclude everything else.
- [ ] Run with `fail_on_revert = true` until the per-selector table shows every selector
      executing.
- [ ] Read the calls/reverts/discards table on every run, not only on failure.
- [ ] Convert every counterexample into a named unit test, with the seed in a comment.
- [ ] **Gate — every selector in the table has non-reverting calls, every invariant has been
      seen to fail at least once against deliberately broken code, and each recorded
      counterexample has a regression test.**

<!-- sources: foundry-book, pashov-fizz, tob-property-testing, crytic-properties, max-taylor-sol -->
