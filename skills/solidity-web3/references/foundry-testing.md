# Foundry testing

Verified against: forge 1.8.1 (commit 982849d314), solc 0.8.36 and 0.8.37,
OpenZeppelin Contracts 5.7.0.

## Contents

- [Project configuration](#project-configuration)
- [Naming so the suite is filterable](#naming-so-the-suite-is-filterable)
- [What a green suite does not prove](#what-a-green-suite-does-not-prove)
- [Assert the specific revert](#assert-the-specific-revert)
- [OpenZeppelin 5.x revert shapes](#openzeppelin-5x-revert-shapes)
- [Cheatcodes worth knowing precisely](#cheatcodes-worth-knowing-precisely)
- [Fuzzing](#fuzzing)
- [Attacker contracts](#attacker-contracts)
- [Fork tests](#fork-tests)
- [Coverage](#coverage)
- [forge lint and forge fmt](#forge-lint-and-forge-fmt)
- [Reading a trace](#reading-a-trace)
- [CI](#ci)

## Project configuration

```toml
[profile.default]
src = "src"
test = "test"
libs = ["lib"]
solc = "0.8.37"                 # pin; see below
evm_version = "cancun"
optimizer = true
optimizer_runs = 200
gas_reports = ["*"]

[profile.ci]
fuzz = { runs = 10_000 }
invariant = { runs = 1_000, depth = 500 }

[rpc_endpoints]
mainnet = "${MAINNET_RPC_URL}"
```

Pin `solc`. On a clean machine forge 1.8.1 compiled `pragma ^0.8.24` with **0.8.36**, downloading
it on demand, although 0.8.37 was released; after `forge build --use 0.8.37` fetched 0.8.37, a
`forge clean && forge build --force` selected 0.8.37. `[verified]` Unpinned, the bytecode you
test is a property of which compiler the machine happens to have.

Dependencies go in with a tag, never a floating branch:

```bash
forge install OpenZeppelin/openzeppelin-contracts@v5.7.0
forge install OpenZeppelin/openzeppelin-contracts-upgradeable@v5.7.0
```

`forge install` requires the project to be a git repository (it uses submodules) and fails with
`fatal: not a git repository` otherwise. `[verified]` For OpenZeppelin 5.x remap **both**
packages — the upgradeable package's `Initializable.sol` and `UUPSUpgradeable.sol` are re-export
shims that import from `@openzeppelin/contracts/`:

```
@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/
@openzeppelin/contracts-upgradeable/=lib/openzeppelin-contracts-upgradeable/contracts/
forge-std/=lib/forge-std/src/
```

## Naming so the suite is filterable

| Prefix | Meaning |
|---|---|
| `test_` | unit test |
| `testFuzz_` | fuzz test (has parameters) |
| `testFork_` | needs an RPC endpoint |
| `test_RevertWhen_` / `test_RevertIf_` | expects a specific revert |
| `invariant_` | invariant assertion, run by the invariant engine |

`testFail*` is deprecated — it passes when *anything* reverts, which is the same defect as a
bare `vm.expectRevert()`. Use `test_RevertWhen_…` with an explicit expectation.

The payoff is `forge test --match-test`, `--match-contract` and `--match-path`, plus being able
to exclude the fork tests when there is no RPC (`--no-match-test testFork`).

## What a green suite does not prove

Read a suite for what it cannot fail. On the fixture suite (`evals/files/Vault.t.sol`), six
tests pass and none of them could ever catch the drain, because:

- There is no attacker contract, so no test ever re-enters. Reentrancy is invisible to
  EOA-driven tests.
- `vm.expectRevert()` with no argument accepts any revert.
- `payFees`, `distribute`, `setRewardHook` and the `receive()` fallback are never called.
- `forge coverage` on that suite reports `src/Vault.sol` at 63.83% lines, 35.00% branches — and
  the untested branches are exactly the vulnerable ones. `[verified]`

Also on that fixture: `test_SetFeeBps` **fails** even though the test contract is the vault's
owner, because `setFeeBps` checks `tx.origin` and `vm.prank(owner)` sets only `msg.sender`.
`vm.prank(owner, owner)` sets both. The right response is to fix the contract, not the prank.
`[verified]`

## Assert the specific revert

```solidity
vm.expectRevert();                                          // accepts ANY revert
vm.expectRevert(bytes("transfer failed"));                  // reason string
vm.expectRevert(Vault.NothingToWithdraw.selector);          // custom error, no args
vm.expectRevert(abi.encodeWithSelector(
    Vault.InsufficientBalance.selector, 1 ether, 0));       // custom error with args
vm.expectRevert(stdError.arithmeticError);                  // Panic(0x11)
vm.expectRevert(stdError.divisionError);                    // Panic(0x12)
```

A bare expectation passes on the wrong revert: a fixture test "proving" that a non-owner cannot
mint passed because of the *access-control* error — the same test would pass if the function
reverted for any other reason. `[verified]` `stdError` requires an explicit import:
`import {Test, stdError} from "forge-std/Test.sol";`, otherwise the compiler reports
`Undeclared identifier`. `[verified]`

`vm.expectRevert` applies to the **next call**, so put it immediately before the call, after any
`vm.prank`. For events, `vm.expectEmit(true, true, true, true)` then the expected `emit` then
the call.

## OpenZeppelin 5.x revert shapes

Measured against 5.7.0 `[verified]`:

| Condition | Revert |
|---|---|
| non-owner calls `onlyOwner` | `OwnableUnauthorizedAccount(address account)` |
| `transferOwnership(address(0))` | `OwnableInvalidOwner(address(0))` |
| ERC-20 transfer beyond balance | `ERC20InsufficientBalance(address sender, uint256 balance, uint256 needed)` |
| ERC-20 spend beyond allowance | `ERC20InsufficientAllowance(address spender, uint256 allowance, uint256 needed)` |
| reentrant call into `nonReentrant` | `ReentrancyGuardReentrantCall()` |
| `initializer` on an initialized contract | `InvalidInitialization()` |
| missing role | `AccessControlUnauthorizedAccount(address account, bytes32 neededRole)` |

Every test asserting a 4.x string (`"Ownable: caller is not the owner"`,
`"ReentrancyGuard: reentrant call"`) either fails or, with a bare `expectRevert`, passes
without testing anything.

## Cheatcodes worth knowing precisely

| Cheatcode | Note |
|---|---|
| `vm.prank(a)` | next call only, `msg.sender` only |
| `vm.prank(a, b)` | sets `tx.origin` too — needed for `tx.origin` checks |
| `vm.startPrank(a)` / `vm.stopPrank()` | for a block of calls; do not nest |
| `vm.deal(a, x)` | set ETH balance; `deal(token, a, x)` (forge-std) sets an ERC-20 balance by writing storage |
| `vm.warp(t)` / `vm.roll(n)` | absolute timestamp / block number, not deltas |
| `vm.store(c, slot, v)` / `vm.load(c, slot)` | raw storage; how to read an ERC-1967 slot or force a state |
| `makeAddr("alice")` | deterministic labelled address — labels appear in traces |
| `makeAddrAndKey("signer")` | address plus its private key, for `vm.sign` |
| `vm.expectCall(target, data)` | asserts a call is made |
| `vm.mockCall(target, data, ret)` | stubs a dependency — useful, but it proves your assumption, not the chain's |
| `vm.snapshotState()` / `vm.revertToState(id)` | cheaper than re-running `setUp` for many variants |
| `vm.createSelectFork("mainnet")` | fork by `[rpc_endpoints]` alias, optionally at a block |
| `vm.envUint("PRIVATE_KEY")` | do not use for real keys — use `--account` with a keystore |

`vm.sign` uses a test key; never put a real private key in a test, a script or an environment
file. Fixtures use obvious placeholders such as `0xREDACTED`.

## Fuzzing

```solidity
function testFuzz_DepositThenWithdraw(uint96 amount) public {
    amount = uint96(bound(amount, 1, 100 ether));   // map, do not reject
    vm.deal(alice, amount);
    vm.prank(alice);
    vault.deposit{value: amount}();
    vm.prank(alice);
    vault.withdrawAll();
    assertEq(alice.balance, amount);
}
```

- `bound(x, lo, hi)` maps the input into range. `vm.assume(cond)` discards the run and counts
  against `max_test_rejects` (default 65536), so a narrow `assume` produces a test that mostly
  does nothing. Use `assume` only to exclude specific values (`address(0)`, the cheatcode
  address, the test contract). `[official]`
- Defaults: `[fuzz] runs = 256`, `fail_on_revert = true`. Raise `runs` in CI, not locally.
  `[official]`
- Narrow the parameter type (`uint96`, `uint32`) so the generator spends its runs in the
  interesting range instead of on astronomical values.
- A failure prints the counterexample and a `Fuzz seed:`; re-run with `--fuzz-seed <seed>` to
  reproduce, and keep the counterexample as a named unit test.

## Attacker contracts

Reentrancy, callback and hook bugs need a contract in the test file, not a cheatcode:

```solidity
contract Drainer {
    Vault public vault;
    constructor(Vault v) { vault = v; }
    function attack() external payable {
        vault.deposit{value: msg.value}();
        vault.withdrawAll();
    }
    receive() external payable {
        if (address(vault).balance >= 1 ether) vault.withdrawAll();
    }
}
```

Assert the *outcome*, not the mechanism: `assertGt(address(drainer).balance, 1 ether)` — the
attacker ends up with more than it put in. Measured on the fixture, the drainer turned 1 ETH
into 12 ETH with 10 reentrant hits. `[verified]` The same pattern with a storage-writing
`receive()` proves the 2300-gas stipend failure, and one that only *reads* state during the
callback proves read-only reentrancy.

## Fork tests

```solidity
function setUp() public { vm.createSelectFork("mainnet"); }

function testFork_FeedIsFresh() public view {
    (, int256 answer,, uint256 updatedAt,) = feed.latestRoundData();
    assertGt(answer, 0);
    assertLt(block.timestamp - updatedAt, 3600);
}
```

Notes from a real run against mainnet: the fork inherits the remote block's timestamp, so
`block.timestamp - updatedAt` was 948 seconds; `vm.warp(updatedAt + 30 days)` left the feed's
`updatedAt` unchanged, which is exactly how a staleness bug is demonstrated. `[verified]`

- Pin the block (`vm.createSelectFork("mainnet", 25953358)`) for anything asserting a value, so
  the test does not start failing when the chain moves. Leave it unpinned only for shape
  assertions.
- Fork tests need `[rpc_endpoints]`; without one the test errors rather than skipping. Keep them
  behind a `testFork` prefix so `--no-match-test testFork` gives a working offline suite.
- `vm.createFork` creates without selecting; `vm.selectFork(id)` switches. State is per-fork.
- A mocked dependency tests your belief about it. A fork tests the dependency. Use fork tests
  for every external token, feed, pool and proxy the protocol actually depends on.

## Coverage

```bash
forge coverage --no-match-coverage "(test|script|lib)"
forge coverage --report lcov          # for CI tooling
forge coverage --ir-minimum           # fallback when the stack-too-deep error hits
```

Read the branch column, not the line column: the fixture suite showed 63.83% lines but 35.00%
branches, and the missing branches were the vulnerable paths. `[verified]` A coverage *failure*
(the tool erroring out) says nothing about whether tests exist — report it as a tooling problem,
not as a testing gap.

## forge lint and forge fmt

`forge build` in 1.8.1 runs the linter and prints notes inline. Measured categories on the
fixtures: `custom-errors` (string `require`), `calls-loop` (external call in a loop),
`erc20-unchecked-transfer`, `unchecked-call`, `literal-instead-of-constant`. `[verified]`

```bash
forge fmt              # rewrite
forge fmt --check      # exit non-zero on a diff — the CI form
forge build --sizes    # per-contract deployed size against the 24 KB limit
```

`forge lint` overlaps Slither on the cheap categories and misses everything semantic; it is a
build-time hygiene gate, not a security tool.

## Reading a trace

```
├─ [37759] Vault::payFees(1000000000000000000 [1e18])
│   ├─ [2300] HungryRecipient::receive{value: 1000000000000000000}()
│   │   └─ ← [OutOfGas] EvmError: OutOfGas
│   └─ ← [Revert] EvmError: Revert
```

`-v` levels: `-vv` shows `console2.log` output and per-test gas, `-vvv` adds traces for failing
tests, `-vvvv` adds traces for all tests, `-vvvvv` adds setup traces. The bracketed number
before each call is the gas *forwarded*, which is how a stipend problem becomes visible rather
than inferred; `←` shows the return, including `[OutOfGas]`, `[Revert]` and the decoded custom
error. Label addresses with `makeAddr` or `vm.label` or the trace is a wall of hex.

## CI

```bash
forge fmt --check
forge build --sizes                   # fails if a contract exceeds 24 KB
forge test                            # default profile
FOUNDRY_PROFILE=ci forge test         # higher fuzz and invariant budgets
forge coverage --report summary
slither . --exclude-dependencies
```

Keep the fuzz and invariant budgets in a `ci` profile so local runs stay fast, and pin the
Foundry version in CI (`foundry-toolchain` with a version, not `nightly`) so a toolchain release
cannot change what "passing" means.

<!-- sources: foundry-book, tenequm-foundry, max-taylor-sol, pashov-fizz, oz-contracts -->
