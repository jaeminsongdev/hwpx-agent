# P06-09 table thousands HWPX policy v1

Status: exact current-target native-source HWPX integration passed; direct-output target/render oracle not run

## Scope

This policy covers the preserving HWPX adapter for:

- `TABLE-032` / `table.thousands_add`
- `TABLE-033` / `table.thousands_remove`

The only admitted native profile is a complete, unmerged table grid containing an explicitly
selected Hangul 2020 formula field whose native formula is `=SUM(LEFT)`. The current licensed target
is Hangul 2020 build `11.0.0.9136`, x86, `ko-KR` on this PC. Other formula shapes, inferred formats,
merged selected cells, ambiguous numeric strings and other Hancom versions fail closed.

## Native mapping

Attempt `20260913-11` created a disposable 1-by-3 table, entered two fixed operands, authored the
horizontal sum, selected exactly the formula cell, and ran the documented native actions
`TableDeleteComma` and `TableInsertComma`. All three HWPX saves passed under the bounded watchdog.

Offline ZIP comparison establishes the exact current-target rule:

- `ResultFormat`, `Formula`, `LastResult`, packed `Command`, field identities and the numeric cache
  remain byte-identical;
- `remove` changes only the selected field's visible result text from grouped to plain digits;
- `add` restores only that visible result text;
- baseline and added `Contents/section0.xml` are byte-identical.

The adapter therefore owns only the selected visible-result byte spans. It does not rewrite or
invent native formula metadata.

## Binding and preservation

`hwpx-agent.table-thousands-hwpx/v1` binds the exact section SHA-256, selected formula state,
complete nonmerged grid, document-flow SHA-256 and domain plan SHA-256 at request time. The lowerer
re-reads and rechecks every binding at build time, applies bounded non-overlapping edits, and then
reopens the result through the typed reader.

The selected owner, AST, numeric cache value, decimal places and every non-grouping property remain
exact. Complete cell payload/properties, table properties, edges, other formula fields, captions,
pagination and bytes outside the selected visible results are protected by the full section and
unowned-byte digests. Requests and receipts use bounded deterministic JSON, and Debug output redacts
all digests, formula metadata and document content.

## Evidence and promotion rule

The six Rust adapter tests cover happy path, idempotence, decimal/negative boundary, request/build
drift, malformed native profiles, bounded strict JSON, stable errors, preservation and redacted
Debug. The source harness static suite passes 23/23, and the exact-source oracle proves both direct
section outputs byte-for-byte equal to the native Hangul results.

This evidence promotes only TABLE-032 and TABLE-033 to `direct_hwpx / integration_passed` with
`schema`, `semantic_reopen` and `formula_readback`. It does not claim direct-output package
save/reopen, PDF/render, rollback/retry, product automation-route runtime, release enablement,
arbitrary-document compatibility, P06-09/P06 completion, production or product completion.

Attempts 01-10 remain failed or interrupted evidence. Attempt 10 exposed a watchdog phase-vocabulary
defect after the native saves had completed; it remains failed and is not relabeled. The corrected
attempt 11 is independently admitted by the exact contract and receipt.
