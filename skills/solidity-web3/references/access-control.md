# Access control

Verified against: OpenZeppelin Contracts 5.7.0, solc 0.8.37, Foundry 1.8.1.

## Contents

- [Start from an inventory](#start-from-an-inventory)
- [Ownable and Ownable2Step in 5.x](#ownable-and-ownable2step-in-5x)
- [AccessControl and role layering](#accesscontrol-and-role-layering)
- [tx.origin is never authorization](#txorigin-is-never-authorization)
- [The insider question](#the-insider-question)
- [Timelocks and who holds the key](#timelocks-and-who-holds-the-key)
- [Initialization is access control](#initialization-is-access-control)
- [Signature-based authorization](#signature-based-authorization)
- [Pausing and emergency powers](#pausing-and-emergency-powers)
- [Reviewing for it](#reviewing-for-it)

## Start from an inventory

Before reading any function body, produce the table. It is the artefact that makes a missing
check visible, because the empty cell is the finding:

| Function | Visibility | Guard | Role holder today | Worst single call |
|---|---|---|---|---|
| `setFeeRecipient` | external | **none** | anyone | redirect the whole fee stream |
| `setFeeBps` | external | `tx.origin == owner` | any contract the owner touches | fee to 100% |
| `payFees` | external | `msg.sender == owner` | deployer EOA | drain to `feeRecipient` |
| `withdrawAll` | external | permissionless by design | anyone | — |

On the fixture vault, `setFeeRecipient` has no check at all while its neighbours do, which is
the shape a real omission takes: not a contract with no access control, but one function in a
group that forgot. Slither reported only a missing zero-address check on that line and said
nothing about the missing owner check. `[verified]`

Every row must end in either a named role or the words "permissionless by design". A function
whose guard you cannot state is a finding.

## Ownable and Ownable2Step in 5.x

```solidity
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";

contract Vault is Ownable2Step {
    constructor(address initialOwner) Ownable(initialOwner) {}
}
```

`Ownable`'s constructor takes the initial owner and there is no zero-argument form: omitting it
is compiler error 3415, `No arguments passed to the base constructor. Specify the arguments or
mark "…" as abstract.` `[verified]` Carried-over 4.x code that writes `contract X is Ownable`
with a bare `constructor() {}` does not compile, which is the good case; the bad case is a test
suite that still asserts the 4.x revert string.

The revert is `OwnableUnauthorizedAccount(address account)`, and
`transferOwnership(address(0))` reverts `OwnableInvalidOwner(address(0))` — use
`renounceOwnership()` if that is really the intent. Asserting `"Ownable: caller is not the
owner"` against 5.x tests nothing. `[verified]`

Prefer `Ownable2Step` for anything holding value: `transferOwnership` only nominates, and the
new owner must call `acceptOwnership()`. A one-step transfer to a mistyped or uncontrolled
address is unrecoverable, and this is a large share of real "governance lost" incidents.

## AccessControl and role layering

```solidity
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
bytes32 public constant PARAM_ROLE  = keccak256("PARAM_ROLE");
```

Layer by blast radius, not by job title. A useful split for a protocol holding funds:

| Tier | Powers | Holder |
|---|---|---|
| Guardian | pause, cancel a queued action | hot multisig or automated monitor, 1-of-n is acceptable |
| Operator | routine parameter moves inside hard-coded bounds | multisig, no timelock |
| Governor | move funds, change bounds, upgrade | multisig **behind a timelock** |

Two failure modes specific to `AccessControl`:

- `DEFAULT_ADMIN_ROLE` can grant itself every other role, so a "restricted" operator role is
  worth nothing if the admin key is the same key. Check `getRoleAdmin` for each role, not just
  the role holders.
- `renounceRole(DEFAULT_ADMIN_ROLE, msg.sender)` from the only admin permanently bricks role
  administration. Bricking is not always a bug — sometimes it is the decentralization
  commitment — but it must be deliberate and documented, and `AccessControlDefaultAdminRules`
  exists for a delayed, non-instant transfer.

Bound the parameters in code rather than trusting the role: `if (bps > 1000) revert
FeeTooHigh(bps);` makes "operator sets fee to 100%" impossible instead of merely unlikely.

## tx.origin is never authorization

```solidity
function setFeeBps(uint16 bps) external {
    require(tx.origin == owner, "not owner");   // broken
    feeBps = bps;
}
```

Any contract the owner interacts with can call this in the same transaction. The fixture proves
it: a `Relay` contract calling `setFeeBps(10000)` succeeded while `tx.origin` was the owner,
setting the fee to 100%. `[verified]` It also breaks smart-contract wallets, ERC-4337 accounts
and EIP-7702 delegated EOAs, where `tx.origin` is a bundler or the account itself.

The only legitimate uses of `tx.origin` are logging and refund accounting, and even there it is
usually the wrong value. `msg.sender == tx.origin` as an "EOA only" anti-MEV check is likewise
obsolete under EIP-7702 and hostile to every smart account.

A side effect worth knowing while testing: `vm.prank(owner)` sets only `msg.sender`, so a
`tx.origin` check fails under `forge test` even when the caller is the owner. The two-argument
`vm.prank(owner, owner)` sets both. If a test needs that, the production code has a
`tx.origin` bug. `[verified]`

## The insider question

Run each privileged function through: *assume the check passes and the holder is hostile — what
does one transaction do?* A role that can move user funds, mint unbounded supply, set a fee to
100%, or point an oracle at an attacker-controlled address is a finding even when the holder is
a reputable multisig, because the answer to "what if the key leaks" is the same either way.

Report it with the mitigation that shrinks the power, not the one that adds trust: hard-coded
bounds, a timelock the community can exit during, a per-transaction or per-epoch cap, or
splitting the role.

## Timelocks and who holds the key

`TimelockController` matters only if the delay applies to the dangerous action, not to the role
transfer. A common misconfiguration delays `grantRole` while leaving the parameter setter
instant; the attacker uses the instant path. Check, for each dangerous function, whether the
*call* is delayed.

Then check who holds the key on-chain rather than in the documentation:
`cast call <contract> "owner()(address)"`, `cast call <contract> "hasRole(bytes32,address)(bool)"`,
and `cast code <owner>` — an owner with no code is an EOA, whatever the README says.

## Initialization is access control

For anything behind a proxy, the initializer *is* the constructor and it is a public function
guarded only by a storage flag:

- `_disableInitializers()` in the implementation's constructor, or anyone initializes the
  implementation and becomes its owner. Verified on the fixture: an arbitrary address called
  `initialize` on the implementation and `owner()` returned that address. `[verified]`
- Deploy and initialize in one transaction (the proxy constructor's `data` argument), or the
  window between them is a front-running race for ownership.
- `initializer` reverts `InvalidInitialization()` once used; post-upgrade state needs
  `reinitializer(n)`. `[verified]`

Details are in the proxy-upgrade topic.

## Signature-based authorization

When a signature replaces an on-chain check, the signature becomes the access control:

- **Replay across calls.** Include a nonce, consume it, and check it before recovery.
- **Replay across chains and contracts.** Use EIP-712 with a domain separator containing
  `chainId` and `address(this)`, and recompute the separator if `chainId` can change (a fork).
- **Malleability.** `ecrecover` accepts both `s` and `n - s`. Bound `s` to the lower half or use
  OpenZeppelin `ECDSA.recover`, which reverts on a high `s` and on a zero recovery.
- **The zero address.** A failed `ecrecover` returns `address(0)`; comparing the result against
  an uninitialized `signer` storage slot authorizes everyone. Never compare against a value that
  can be zero.
- **Contract signers.** An ERC-4337 or Safe account cannot produce an ECDSA signature. Support
  EIP-1271 `isValidSignature` if contracts are expected to sign; OpenZeppelin's
  `SignatureChecker` handles both.
- **Deadlines.** Every signed authorization carries an expiry, or a leaked signature is valid
  forever.
- **Signed-data ambiguity.** `abi.encodePacked` over two dynamic fields lets `("ab","c")` and
  `("a","bc")` hash identically; use `abi.encode`, or hash each dynamic field first.

## Pausing and emergency powers

A pause is only useful if it covers the paths that lose money. Check coverage explicitly: if
`deposit` is pausable but `withdraw` and the liquidation path are not, pausing during an
incident freezes the victims and not the attacker. Write the pause coverage into the inventory
table as its own column, and make sure unpausing is not a single EOA's decision.

## Reviewing for it

- [ ] Build the inventory table. Every external and public function gets a row, including
      `receive`/`fallback` and anything reachable by `delegatecall`.
- [ ] For each guard, name the exact check (`msg.sender ==`, modifier, role) and read the
      modifier's body rather than trusting its name.
- [ ] Check `getRoleAdmin` for every role, and whether one key holds several tiers.
- [ ] Check each parameter setter for hard bounds; an unbounded setter is a finding.
- [ ] Run the insider question on every privileged function and record the answer.
- [ ] Resolve every key holder on-chain, and note which are EOAs.
- [ ] For any signature path, walk the six replay and malleability items above.
- [ ] **Gate — no function lacks a stated guard, every role's admin is identified, the pause
      coverage is written down, and each finding names the actor and the single call.**

<!-- sources: oz-contracts, oz-skills, pashov-auditor, pashov-xray, nuwrldnf8r-audit, layerghost-kit, cyfrin-solskill -->
