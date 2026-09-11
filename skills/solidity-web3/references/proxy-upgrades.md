# Proxy upgrades

Verified against: OpenZeppelin Contracts / Contracts-Upgradeable 5.7.0, solc 0.8.37,
Foundry 1.8.1, Slither 0.11.6.

## Contents

- [Identify the pattern from chain state](#identify-the-pattern-from-chain-state)
- [Choosing between UUPS, Transparent and Beacon](#choosing-between-uups-transparent-and-beacon)
- [Storage layout is the ABI of an upgrade](#storage-layout-is-the-abi-of-an-upgrade)
- [What a collision actually looks like](#what-a-collision-actually-looks-like)
- [Namespaced storage: ERC-7201](#namespaced-storage-erc-7201)
- [Initializers](#initializers)
- [Constructors and immutables do not exist](#constructors-and-immutables-do-not-exist)
- [Upgrade authorization](#upgrade-authorization)
- [The 5.x import shims](#the-5x-import-shims)
- [Verification before deploying](#verification-before-deploying)
- [Upgrade checklist](#upgrade-checklist)

## Identify the pattern from chain state

The repository tells you what someone intended; the proxy tells you what is deployed. Read the
ERC-1967 slots:

```solidity
// keccak256("eip1967.proxy.implementation") - 1
bytes32 constant IMPL_SLOT  = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
// keccak256("eip1967.proxy.admin") - 1
bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
// keccak256("eip1967.proxy.beacon") - 1
bytes32 constant BEACON_SLOT = 0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50;
```

`IMPL_SLOT` equals `ERC1967Utils.IMPLEMENTATION_SLOT` in 5.7.0, and reading it on a fixture
proxy returned the implementation address. `[verified]` Off-chain: `cast storage <proxy>
0x3608…2bbc --rpc-url <url>`, or in a test `vm.load(proxy, IMPL_SLOT)`.

A non-zero admin slot means Transparent; a non-zero beacon slot means Beacon; neither, with
`upgradeToAndCall` on the implementation, means UUPS.

## Choosing between UUPS, Transparent and Beacon

| | UUPS | Transparent | Beacon |
|---|---|---|---|
| Upgrade logic lives in | the implementation | the proxy + its `ProxyAdmin` | a shared beacon |
| Cost per call | cheapest | one extra `SLOAD` on the admin check | one extra call to the beacon |
| Failure mode that bricks it | shipping an implementation without `UUPSUpgradeable` | none of this kind | a bad beacon bricks every proxy at once |
| Use when | one or few proxies, and you control the release process | you want the upgrade path outside the logic | many identical proxies upgraded together |

Default to UUPS for a small number of contracts and accept its one sharp edge: every future
implementation must keep inheriting `UUPSUpgradeable` with a working `_authorizeUpgrade`, or the
proxy loses the ability to upgrade permanently. Use Transparent when the release process is
unreliable enough that this matters. In 5.x `TransparentUpgradeableProxy` deploys its own
`ProxyAdmin` and its constructor's second parameter is that admin's **owner**, not the admin
address — a 4.x call site passing an existing `ProxyAdmin` there silently makes the admin
contract the owner. `[official]`

## Storage layout is the ABI of an upgrade

Rules, in order of how often they are broken:

1. **Append only.** New variables go after every existing one.
2. **Never reorder, never remove, never change a type's width.** Removing a variable shifts
   everything after it exactly like inserting does.
3. **Adding a variable in the middle of an inherited chain shifts the child's variables.**
   Adding a variable to a base contract is the same defect as inserting one locally.
4. **Changing a `struct`'s fields, or an array's element type, relocates everything after it.**
5. **A `mapping`'s values are hashed by slot number**, so moving the mapping declaration
   orphans every existing entry — the data is still there, unreachable.
6. `constant` and `immutable` occupy no storage, so converting a storage variable to
   `immutable` removes a slot and shifts the rest.

## What a collision actually looks like

The fixture (`evals/files/StakingUpgradeable.sol`) prepends two variables in V2. Layouts from
`forge inspect src/StakingUpgradeable.sol:StakingV1 storage-layout`:

```
| Name         | Type                        | Slot |        | Name         | Type       | Slot |
| stakingToken | contract IERC20             | 0    |        | rewardRate   | uint256    | 0    |
| totalStaked  | uint256                     | 1    |   V2:  | treasury     | address    | 1    |
| stakedOf     | mapping(address => uint256) | 2    |        | stakingToken | IERC20     | 2    |
| cooldown     | uint256                     | 3    |        | totalStaked  | uint256    | 3    |
                                                            | stakedOf     | mapping    | 4    |
                                                            | cooldown     | uint256    | 5    |
```

After upgrading a proxy whose `totalStaked` held 7 ether and whose `cooldown` held 7 days:

```
V1 totalStaked  (slot 1) 7000000000000000000
V2 treasury     (slot 1) 0x0000000000000000000000006124feE993BC0000
V2 totalStaked  (slot 3) 604800
rewardRate seen through proxy 57005          // the old stakingToken address, 0xdead
```

`[verified]` Note what this is not: it is not a revert, not a zeroed balance, not anything a
smoke test notices. `treasury` becomes an address derived from an amount, `totalStaked` becomes
a duration, and `sweepToTreasury` now sends tokens to `0x…6124feE993BC0000`. The contract keeps
working and the numbers are wrong.

Note also that V1's own variables start at slot 0 even though it inherits `OwnableUpgradeable`
and `UUPSUpgradeable`: in 5.x those bases keep their state in ERC-7201 namespaces, so they
consume no sequential slots and no `__gap` arrays are needed. `[verified]` A 4.x-era mental
model that expects 50-slot gaps will mis-predict every layout.

## Namespaced storage: ERC-7201

For new upgradeable code, put your own state in a namespace too. The location is
`erc7201(id) = keccak256(keccak256(id) - 1) & ~0xff`, which in Solidity is:

```solidity
/// @custom:storage-location erc7201:acme.storage.Staking
struct StakingStorage {
    IERC20 stakingToken;
    uint256 totalStaked;
    mapping(address => uint256) stakedOf;
}

// keccak256(abi.encode(uint256(keccak256("acme.storage.Staking")) - 1)) & ~bytes32(uint256(0xff))
bytes32 private constant STAKING_STORAGE =
    0x…;

function _s() private pure returns (StakingStorage storage $) {
    assembly { $.slot := STAKING_STORAGE }
}
```

`[official]` (ERC-7201). The `- 1` avoids the slot Solidity itself would use for
`keccak256(id)`, and the second hash keeps a namespace larger than one slot from extending into
`keccak256(id) + n`. The `&  ~0xff` alignment leaves 256 slots of room per namespace. solc
records the annotation in the AST from 0.8.20, which is why the upgrade-safety tooling can check
it; the compiler enforces nothing, so the annotation is a promise you keep by construction.

Adding a field to the end of a namespaced struct is safe. Deleting a whole namespace is not
detectable as safe by the tooling and has no targeted suppression.

## Initializers

```solidity
contract StakingV1 is Initializable, OwnableUpgradeable, UUPSUpgradeable {
    constructor() { _disableInitializers(); }

    function initialize(IERC20 token, address owner_) external initializer {
        __Ownable_init(owner_);
        stakingToken = token;
    }
}
```

- `_disableInitializers()` in the constructor sets the initialized version to `type(uint64).max`
  on the *implementation*, so nobody can initialize it directly. Without it, an arbitrary
  address initialized the fixture implementation and became its owner. `[verified]`
- `__Ownable_init(initialOwner)` takes the owner explicitly in 5.x.
- There is **no** `__UUPSUpgradeable_init()` in 5.x. Calling it — as 4.x code does — fails with
  compiler error 7576, `Undeclared identifier`. `[verified]`
- Every `__X_init` must be called exactly once, in the order the inheritance implies, and only
  from a function carrying `initializer` or `reinitializer` (they are `onlyInitializing`).
- Post-upgrade state uses `reinitializer(2)`, `reinitializer(3)`, … An `initializer`-modified
  function called on an already-initialized proxy reverts `InvalidInitialization()`.
  `[verified]`
- Initialize in the same transaction as the deployment: `new ERC1967Proxy(impl,
  abi.encodeCall(StakingV1.initialize, (token, owner)))`.

## Constructors and immutables do not exist

Constructor code runs against the implementation's storage, not the proxy's. A V2 constructor
setting `rewardRate = 100` read back as `57005` through the proxy — the old `stakingToken`
address in slot 0. `[verified]` The same applies to `immutable`: the value is in the
implementation's bytecode, which is shared, so it cannot depend on per-proxy state.

Anything a proxy user must see belongs in an initializer. If a value genuinely is
per-implementation (a hard-coded chain id, a fixed decimals), mark it
`@custom:oz-upgrades-unsafe-allow state-variable-immutable` so the tooling records that you
meant it.

## Upgrade authorization

```solidity
function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
```

An empty override is a live vulnerability, not a style problem. On the fixture, an arbitrary
address called `upgradeToAndCall(evil, "")` on the proxy and the implementation slot changed to
the attacker's contract. `[verified]` Every review of a UUPS contract checks this function's
body first.

Other authorization facts for 5.x:

- `upgradeTo(address)` was removed; only `upgradeToAndCall(address,bytes)` remains. A static
  call to `upgradeTo` on a 5.x proxy fails. `[verified]`
- `UUPSUpgradeable` guards against being called on the implementation directly (`onlyProxy`) and
  against `delegatecall` into `upgradeToAndCall` from a non-ERC-1967 context
  (`notDelegated` on `proxiableUUID`).
- Upgrade authority on a live protocol belongs to a multisig behind a timelock. An EOA holding
  it means one leaked key rewrites the contract.

## The 5.x import shims

In 5.7.0, `@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol` and
`.../UUPSUpgradeable.sol` are two-line re-export shims that import from
`@openzeppelin/contracts/...`. `[verified]` Consequences:

- A project remapping only `@openzeppelin/contracts-upgradeable/` fails to resolve the import.
  Remap both packages.
- OpenZeppelin states these aliases will be removed in the next major version, so new code
  should import `Initializable` and `UUPSUpgradeable` from `@openzeppelin/contracts` directly.
  `[official]`
- Upgrading a proxy from a 4.x implementation to a 5.x one is not supported: 4.x used sequential
  storage with gaps and 5.x uses ERC-7201 namespaces, so the layouts are unrelated. `[official]`

## Verification before deploying

```bash
forge inspect src/Staking.sol:StakingV1 storage-layout > /tmp/v1.txt
forge inspect src/Staking.sol:StakingV2 storage-layout > /tmp/v2.txt
diff /tmp/v1.txt /tmp/v2.txt          # must be append-only

slither-check-upgradeability . StakingV1 --new-contract-name StakingV2
```

On the fixture, `slither-check-upgradeability` (22 detectors in 0.11.6) reported 7 findings and
named the collision precisely — `order-vars-contracts` pairing `StakingV1.totalStaked` with
`StakingV2.treasury`, plus `extra-vars-v2` and `initialize-target`. `[verified]` What it did
**not** report: the empty `_authorizeUpgrade` and the missing `_disableInitializers()`. Run it,
then still read the two functions yourself. `[verified]`

The strongest check is a fork test: fork the chain at a recent block, upgrade the real proxy in
the fork, and re-read balances and invariants through it.

```solidity
function test_UpgradePreservesBalances() public {
    vm.createSelectFork("mainnet");
    uint256 before = Staking(PROXY).stakedOf(WHALE);
    address v2 = address(new StakingV2());
    vm.prank(Staking(PROXY).owner());
    UUPSUpgradeable(PROXY).upgradeToAndCall(v2, "");
    assertEq(StakingV2(PROXY).stakedOf(WHALE), before);
}
```

## Upgrade checklist

- [ ] Pattern identified from the ERC-1967 slots on-chain, not from the repository.
- [ ] Storage diff is append-only; `slither-check-upgradeability` run and every finding
      explained.
- [ ] No new `constructor` state, no new `immutable` that proxy users must see.
- [ ] `_disableInitializers()` in the new implementation's constructor.
- [ ] New state initialized by `reinitializer(n)`, and that call is part of the upgrade
      transaction.
- [ ] `_authorizeUpgrade` gated; the gate's holder is a multisig or timelock, resolved on-chain.
- [ ] New implementation still inherits `UUPSUpgradeable` (for UUPS), or the proxy can never be
      upgraded again.
- [ ] Fork test upgrades the real proxy and re-checks every user-visible balance and every
      protocol invariant.
- [ ] **Gate — the fork test passes and the storage diff shows only appended slots.**

<!-- sources: oz-contracts, oz-skills, erc-7201, pashov-auditor, tob-secure-contracts, slither -->
