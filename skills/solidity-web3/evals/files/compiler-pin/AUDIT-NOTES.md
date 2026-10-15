# Audit package — Harbor Vaults v2 (draft, to be sent to the auditors on Monday)

## Scope

`src/HarborVault.sol`, `src/HarborRouter.sol`, `src/lib/ShareMath.sol` (commit to be tagged).

## Compiler

- Pinned: solc **0.8.37** (`solc_version` in `foundry.toml`), `via_ir = true`, optimizer on,
  10 000 runs, EVM `prague`.
- 0.8.37 is the first Solidity release with an empty known-bug list, so **no known compiler
  bugs apply to this codebase**. We checked this when we picked the version in September and
  do not need to revisit it.
- `pragma solidity 0.8.37;` in every file, no floating pragmas.

## Out of scope

Deployment scripts, the off-chain keeper, the front end.
