# P09-101 SQL oracle diagnostics report

Recorded 2026-10-04 UTC. This is source-only progress, not closure of P84 SQL or P09.

## Implemented

The existing worker now emits bounded owned-fixture context on a completion error, retaining the original error. The existing owned runner can project forty exact-context BOOL/NULL checks after its original environment checks. The application account has no additional privileges. Known-literal filtering prevents arbitrary fixture-error suffixes from entering the receipt. New read-only inheritance validation binds both changed parents to their whole preimages and replays the unmodified preceding audit on that exact prior view.

## Actual checks

| Check | Result and scope |
| --- | --- |
| Rust example unit harness | 4 PASS; no example main or DB executed; terminal `c407ee`, exit 0 |
| Artifact/revision library tests | 25 + 16 PASS; terminal `ba85d0`, exit 0; no SQL connection |
| Python diagnostics/preservation | 14 + 8 = 22 PASS; terminal `ab5717`, exit 0; mocked DB callbacks are not actual SQL |
| Strict example lint | PASS, terminal `ba85d0`; `-D warnings`, offline/locked |
| Current-source component validators | 15 verified, PASS, terminal `19dc65`; green rows 0, Gate OPEN |
| Original default matrix generation check | retained FAIL `matrix_drift`, terminal `967b2b`, exit 1 |
| New Rust formatting / diff whitespace | PASS, `63ba47` / `84c135` |
| Python source parse | 5 files PASS, `9e06af`; no DB/native execution |

Scoped Rust total is 45, not the historical P100 296 rerun. Neither forty diagnostic keys nor 877 pinned current source files are counts of remaining product tasks.

## Failed attempts retained

The first Python check assumed twenty-six AND predicates; the unchanged original has twenty-four. The test was corrected against its pinned complete source without removing predicates. Rust initially used the wrong nested import and failed compilation; corrected to the immediate parent namespace. Both full failed-source preimages remain in `source-archive/p09-101-initial-failure/`; no failed executable was produced. Their terminal results are retained in the initial-failures receipt.

A later read-only conformance command incorrectly sent the current-source option to `reference_conformance.py`; that script rejected the option (`965b87`, exit 1). The proper unchanged validator `validate_reference_conformance_contract.py --current-source-v2` passed (`19dc65`). The original default failure remains failed and was not weakened.

## What remains

P84 earlier `55000` and original SQL-policy-fixture failures are UNRESOLVED. Earlier owned PostgreSQL checks passed 292 unique assertions in each of two rounds, not 584 unique assertions. They do not prove the earlier failure cause or full product acceptance. This stage cannot retrospectively reconstruct missing raw stderr.

New table insertion was inspected but not implemented: its original template/header/native-ID/full-Flow binding must be integrated, rather than supplying guessed bindings or inserting arbitrary XML. P09/A12/A13 remain OPEN, P26 failed-semantic/non-green, P62 unresolved, native input requires re-admission, and 34 native cases remain NOT_RUN/green 0.

At least six coarse non-permission implementation/diagnostic groups remain: metadata/coordinate support; full comment/rich Flow/compiler; durable integration; remaining document semantics; trusted execution/protection/atomic publication; P84 SQL failure investigation. This slice advances the last group but closes none of the six. Native validation is a separate execution boundary. No P10 implementation, commit, push, deletion, move or settings changes were performed.
