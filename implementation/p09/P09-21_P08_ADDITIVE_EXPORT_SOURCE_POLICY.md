# P09-21 exact additive-export source bridge

This is a new dependency-source qualification, not a rewritten P08 PASS receipt or
a fresh target execution. Preserve P08-01/P08-09 validators, contracts, reports,
matrix, original source qualification and all target/failed receipts byte-for-byte.

Nine legacy P08 verifiers pin the whole raw `hwpx-package/src/lib.rs`. P09 added
two module declarations and two public-export blocks. The legacy verifier must
continue to report `implementation_digest` for this changed whole file; it is not
silenced, monkeypatched, normalized or allowed to pretend that the current file has
the old digest. The old aggregate remains a legacy source-lock failure.

## Exact successor admission

- Pin current raw lib `9b1a0b883e0dfa9f99a61762d21d3bf03c98569289e2aba9b36b6d69ae2311d8`.
- Delete only the four explicitly enumerated, uniquely occurring P09 export spans
  **in memory**, never on disk. Require the resulting raw bytes to reproduce
  `a22f9f73f04e17ac3439022fcf6aaa0fb5f5ddb02d48257d10998bd01bdf2e12`.
- Pin the raw predecessor validator/contract/qualification/aggregate source identities.
- Require every non-lib implementation/test file in each of the nine affected
  validators to match its old raw lock exactly, independently of the legacy verdict.
  Every old contract/document/source/qualification rule still runs. Each admitted
  observed failure must contain only `implementation_digest`, exit code 1, verified
  qualification, the complete implementation count, and verified official sources
  where applicable. The legacy failure is stored as failure, never converted to PASS.
- Run every unchanged P08 aggregate matrix/source/privacy/route/unavailable/P11 rule.
- Execute all 23 required upstream validators, plus both current P09 numeric
  and object-caption source validators. Pin all 25 validator source files before
  execution/import. Fourteen unaffected upstream checks and both P09 checks must
  genuinely PASS; exactly nine enumerated legacy lib-lock failures may be qualified
  through the independently proven exact export delta. No check is skipped.
- Re-run the unchanged Rust asset regression tests in the current linked workspace.
  A source-projection match cannot substitute for component or target behavior.
- Reject any other source drift, duplicate/missing export span, changed predecessor,
  missing required validator, weakened contract, changed matrix or claim promotion.

The bridge qualifies only exact additive source compatibility for P09's dependency.
It does not claim that a legacy aggregate command now passes or reexecute P08's
historical target campaigns. Historical current-PC target evidence remains separate
from this source result. P09 row promotion still needs actual semantics/render,
fallback and differential evidence; P09/P10/full-product Gate status is unchanged.

## Receipt and migration

`tools/p09/verify_p08_additive_export_source_bridge.py` emits a new exclusive public
receipt and can reproduce it read-only. The receipt records all 25 actual verdicts,
including the nine failed legacy verdicts and exact current/predecessor identities.
New bridge source/test/policy/migration bytes and every executed validator source
are bound in the result. No trust/registry/network/Hangul/UI operation occurs.

Any additional library/module change requires another explicitly bounded source
successor; a caller-provided new hash cannot authorize new spans or expectations.
Do not relabel old receipts or update old expected hashes to improve PASS counts.

## Preserved initial findings and official source prerequisite

The initial bridge integration test failed on the image validator's identical
full-lib lock; that failure revealed the same lock in eight other validators.
An exhaustive upstream diagnostic also found the drawing/active-content official
reference root missing. Neither error was admitted by the initial bridge.
The reference root was restored from the repository-local clean official source
cache at the already pinned commit `1453388472c703a4b299a0834f425cdac16644b9`,
with raw source bytes verified by both unchanged validators. Drawing canvas now
genuinely passes; active content reports only the preserved lib digest failure.
No reference commit/hash was refreshed, and no junction, environment variable,
registry, trust setting, source cache or original P08 authority was changed.
