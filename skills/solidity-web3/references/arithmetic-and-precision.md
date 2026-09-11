# Arithmetic and precision

Verified against: solc 0.8.37, Foundry 1.8.1, OpenZeppelin Contracts 5.7.0.

## Contents

- [What 0.8 checked arithmetic does and does not cover](#what-08-checked-arithmetic-does-and-does-not-cover)
- [Casts truncate silently](#casts-truncate-silently)
- [Operation order](#operation-order)
- [Rounding direction is a security property](#rounding-direction-is-a-security-property)
- [Decimals](#decimals)
- [Fixed-point conventions](#fixed-point-conventions)
- [Share inflation and the first depositor](#share-inflation-and-the-first-depositor)
- [Packed integers and silent ceilings](#packed-integers-and-silent-ceilings)
- [Signed arithmetic](#signed-arithmetic)
- [Proving it with fuzz tests](#proving-it-with-fuzz-tests)
- [Reviewing a formula](#reviewing-a-formula)

## What 0.8 checked arithmetic does and does not cover

From 0.8.0, `+ - * /` and `%` on integers revert on overflow, underflow and division by zero
with `Panic(0x11)` (arithmetic) and `Panic(0x12)` (division by zero). In Foundry these are
`stdError.arithmeticError` and `stdError.divisionError` — and `stdError` needs an explicit
import from `forge-std/Test.sol`, which is easy to miss. `[verified]`

What it does *not* cover:

- **Explicit casts.** See below. This is the gap people assume is closed.
- **`unchecked` blocks.** Pre-0.8 wraparound semantics, deliberately.
- **Precision loss.** Integer division truncating toward zero is not an error; it is the entire
  problem. No compiler version will ever revert on it.
- **Assembly.** `add`, `mul`, `div` in Yul wrap, and `div` by zero returns 0 rather than
  reverting.
- **The *meaning* of a reverting subtraction.** Turning a drain into a revert is not a fix.

So `SafeMath` is dead, and any review comment recommending it on 0.8 code is noise — but
"the compiler checks arithmetic" is not a reason to skip a formula review.

## Casts truncate silently

```solidity
uint256 big = 2 ** 128 + 7;
uint128 narrow = uint128(big);   // == 7, no revert
```

`[verified]` Implicit narrowing is a compile error, so the only casts in the codebase are the
ones someone wrote on purpose — and each is an unproven claim that the value fits.

```solidity
import {SafeCast} from "@openzeppelin/contracts/utils/SafeCast.sol";
uint128 amount = SafeCast.toUint128(big);   // reverts SafeCastOverflowedUintDowncast(128, big)
```

Casts worth stopping on in review:

| Cast | What is lost |
|---|---|
| `uint128`/`uint112`/`uint96`/`uint64` from `uint256` | the high bits, silently — an amount becomes a small amount |
| `int256` → `uint256` on an oracle answer | a negative price becomes ~1.15e77 |
| `uint256` → `int256` above `type(int256).max` | a positive amount becomes negative |
| `uint32(block.timestamp)` | wraps in 2106; fine for a 32-bit delta, wrong for an absolute deadline |
| `uint8(role)` / `uint16(bps)` from user input | a value above the width silently aliases to a valid one |
| `address(uint160(x))` | any high bits of `x`, which is how a slot value becomes a plausible-looking address |

## Operation order

Integer division truncates, so `(a / b) * c` loses up to `c - 1` units relative to
`(a * c) / b`. The loss is not cosmetic when the intermediate is a rate:

```solidity
// fixture bug
uint256 ratePerSecond = (debt * 5 / 100) / 365 days;
return ratePerSecond * elapsed;
```

Measured on a 1000-unit debt of a 6-decimal asset over one year: the contract charged
`31536000` where the stated 5% is `50000000` — **37% under-charged**, and for any debt below
about 631e6 wei the per-second rate truncates to zero and the position accrues nothing at all.
`[verified]`

Rules:

- Multiply before dividing, and divide exactly once at the end.
- Never precompute a per-second (or per-block) rate by division; keep the numerator whole and
  divide by the period at the end.
- Where the order cannot be changed, use a full-width helper: OpenZeppelin's
  `Math.mulDiv(a, b, denominator)` computes `a * b / denominator` with a 512-bit intermediate
  and a rounding argument, so it neither overflows at `a * b` nor loses the low bits.

Slither's `divide-before-multiply` detector finds the shape but not the significance: on the
fixture it flagged three sites, of which two were WAD-scaling with sub-wei loss and one was the
real 37% bug. Triage each hit by computing the loss. `[verified]`

## Rounding direction is a security property

Truncation always favours somebody. Choose deliberately, and write the direction next to the
formula:

| Quantity | Round | Why |
|---|---|---|
| Shares minted for a deposit | down | the depositor must not receive more than they paid for |
| Assets returned for a redemption | down | the pool must not pay out more than the share is worth |
| Debt owed | up | the borrower must not owe less than they borrowed |
| Collateral required | up | the position must not be under-collateralised by a wei |
| Fees taken | up (to the protocol) or explicitly waived | otherwise a loop of dust trades takes the fee to zero |

The exploit shape is always the same: repeat an operation whose rounding favours the caller until
the accumulated dust is worth more than the gas. A round-trip that returns *more* than it took
is a fuzz property, not a code-review judgement:
`assertLe(convertToAssets(convertToShares(x)), x)`.

## Decimals

There is no rule that tokens use 18 decimals. USDC and USDT use 6, WBTC uses 8, Gemini USD
uses 2, and some rebasing experiments used 24. The failures:

- A hard-coded `1e18` scale applied to a 6-decimal amount is off by 1e12 — the fixture's
  `reserve1 * 1e12` scaling is correct only for the exact 18/6 pair it was written for, and
  silently wrong for every other pool. `[verified]`
- Reading `decimals()` once at construction and caching it is right for an immutable token and
  wrong for a proxied token that upgrades.
- `decimals()` is optional in ERC-20 and reverts on a few tokens; `SafeERC20`-style trial
  decoding or a constructor argument is safer than assuming.
- Chainlink feeds have their own `decimals()`, usually 8 — mixing a 1e8 price with a 1e18 amount
  is a 1e10 error. The fixture's `* 1e10` is that conversion, and it is only right for 8-decimal
  feeds. The measured ETH/USD feed reported `decimals = 8` and an answer of `247209000000`.
  `[verified]`

Never infer decimals from a symbol. Read them, or take them as a constructor parameter and
assert them.

## Fixed-point conventions

Pick one convention per codebase and name it: WAD (1e18), RAY (1e27), or basis points (1e4).
Mixing them is how a fee of 50 becomes 50% instead of 0.5%. Two conventions in one formula is a
review finding even when the arithmetic happens to be right, because the next change breaks it.

Basis-point arithmetic is where the mistakes concentrate: `amount * feeBps / 10_000` is correct;
`amount * feeBps / 100` is a 100x fee; and an unbounded `feeBps` setter makes a 100% fee
reachable, which is an access-control finding as much as an arithmetic one.

## Share inflation and the first depositor

In any `shares = assets * totalSupply / totalAssets` vault, the first depositor controls both
sides of the ratio:

1. Deposit 1 wei, receive 1 share.
2. Transfer (donate) 10_000e18 assets directly to the vault, so `totalAssets` is huge and
   `totalSupply` is 1.
3. The next depositor's `assets * 1 / 10_000e18` truncates to 0 shares, and their deposit is
   absorbed by share number one.

Defences, in order of preference: virtual shares and assets (OpenZeppelin ERC4626's
`_decimalsOffset`), a dead-shares mint at initialization, a minimum first deposit, and a
`require(shares > 0)` that at least converts theft into a revert. Track `totalAssets` internally
rather than reading `token.balanceOf(address(this))`, so a donation cannot move the ratio at all.

## Packed integers and silent ceilings

Packing `uint112 reserve0; uint112 reserve1; uint32 blockTimestampLast;` into one slot is a real
gas win and a real ceiling: `type(uint112).max` is about 5.19e33, so an 18-decimal token with a
supply above ~5.19e15 units cannot be fully held. The cast *into* the packed field is where the
truncation happens, so it needs `SafeCast` even when the logical value obviously fits today.

`uint32` timestamps wrap in 2106. Storing a *delta* in `uint32` is fine (136 years); storing an
absolute deadline is a bug with a distant due date.

## Signed arithmetic

- `type(int256).min` has no positive counterpart: `-x` and `abs(x)` both revert (or, in
  `unchecked`, return `int256.min` again).
- `/` truncates toward zero for negatives, so `-7 / 2 == -3`, not `-4`. Ceiling/floor helpers
  written for unsigned values are wrong here.
- `%` takes the sign of the left operand.
- An oracle's `int256 answer` must be checked `> 0` before casting; a negative or zero answer
  cast to `uint256` becomes an astronomically large price.

## Proving it with fuzz tests

Arithmetic is the one area where fuzzing beats reading, because the boundary is a number:

```solidity
function testFuzz_RoundTripNeverGains(uint256 assets) public {
    assets = bound(assets, 1, 1e30);
    uint256 shares = vault.convertToShares(assets);
    assertLe(vault.convertToAssets(shares), assets);   // never returns more than it took
}

function testFuzz_InterestMatchesRate(uint256 debt, uint256 elapsed) public {
    debt = bound(debt, 1e6, 1e30);
    elapsed = bound(elapsed, 1, 365 days);
    uint256 expected = debt * 5 * elapsed / (100 * 365 days);
    assertApproxEqAbs(desk.accrued(debt, elapsed), expected, 1);   // one wei of truncation
}
```

Use `bound` rather than `vm.assume` for ranges: `assume` throws the run away and counts against
`max_test_rejects` (default 65536), while `bound` maps the input into the range and keeps it.
`[official]`

## Reviewing a formula

- [ ] Write the formula's intent in one sentence of arithmetic, without Solidity. If you cannot,
      that is the finding.
- [ ] Check every division for a truncating intermediate; compute the loss at realistic and at
      minimal magnitudes.
- [ ] Check every cast against the width it targets and the value's real maximum.
- [ ] Decide who each rounding favours, and whether repeating the operation extracts value.
- [ ] Check the decimals of every token and feed involved, at the scaling site.
- [ ] Check the zero case: zero amount, zero supply, zero total, first depositor.
- [ ] Check the maximum case: `type(uint256).max` input, and the packed field's ceiling.
- [ ] **Gate — a fuzz test with `bound` covers each boundary found, and any rounding finding
      states the per-operation loss and the number of repetitions needed to matter.**

<!-- sources: pashov-auditor, oz-contracts, foundry-book, layerghost-kit, mariano-audit, crytic-properties -->
