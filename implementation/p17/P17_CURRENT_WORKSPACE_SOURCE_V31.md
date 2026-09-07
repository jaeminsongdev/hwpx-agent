# P17 current workspace source qualification v31

Date: 2026-09-07

Scope: P06-06 bounded pure FormulaAst/reference/cache/number-format successor only

Decision: **qualified source component only; evaluation, verified oracle cache, HWPX lowering,
Hangul 2020 readback, P06-06/P06 phase, production and product PASS remain false**

The v1-v30 contracts remain byte-for-byte unchanged. This v31 layer composes exact v30 contract
SHA-256 `fe4523ca2141f99574566ff0197e4ac465c5cadc8e4397ca7276854d84e27357`
and binds clean implementation commit
`cc925658d2c08e1a67118fc2a1b426f3c9929651`.

Current-host source acceptance run `7fe87b6cf5ea435ca8f037559d371b0e` passed all 11 checks. Its
canonical receipt SHA-256 is
`98ca665071096c1c1e95ad919b0b0acbf632cbc8928ea39c0ab63ce5f7ae6481`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection and all false runtime/production claims remain
exactly preserved.

The eight bound implementation files add a finite, locale-neutral formula parser and typed AST for
exact decimals, arithmetic, A1 cells/ranges, independent relative/absolute axes and `SUM`, `AVG`,
and `PRODUCT`. Copy/rebase requires exact current grid dimensions. Structural row/column edits bind
exact pre-edit dimensions and checked post-edit dimensions, update both reference kinds, and fail
atomically for invalid edits or deleted owners/endpoints. Formula source, unverified cache and number
format remain separate; this pure boundary cannot manufacture an oracle-qualified cache value.

Formula tests pass 15/15 including a deterministic 256-case edit corpus, exact-grid JSON readback,
cache-policy mismatch and immutability failures. `domain-ir` passes 125/125, the P06 Python contract
suite passes 37/37, full workspace tests pass, formatting is clean and workspace Clippy with warnings
denied passes. No dependency was added.

This source qualification does not claim formula evaluation, dependency/cycle semantics, exact HWPX
formula strings or number-format codes, Hangul recalculation/save/reopen/readback, pagination,
rendering, or P06-06 completion. Those require a target-bound adapter and licensed Hangul 2020 oracle
evidence before the card can close.
