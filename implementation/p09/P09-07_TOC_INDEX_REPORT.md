# P09-07 TOC/index report

Decision: `COMPONENT PASS / OFFICIAL STRUCTURE PARTIALLY QUALIFIED /
UNVERIFIED NATIVE GENERATION SEMANTICS / DIRECT AND TARGET NOT RUN / NON-GREEN`.

## Delivered

- Added `hwpx-agent.toc-index/v1` for P09-owned REF-037/038/039/041/042.
- Added complete multi-level TOC source/mark state, exact native hide transition, index primary and
  subentry state, generated settings, and complete projection-based cache classification.
- Added global native-ID/name collision, anchor containment, key pairing, locale/settings, lock,
  preservation, request/build drift, strict JSON, finite-limit, and redacted-Debug checks.
- Added sealed plan and private tamper test, versioned private contract, migration, pinned-source
  qualification, validator, and contract tamper tests.

## Source result

The clean pinned Hancom OWPML checkout proves `titleMark(ignore)`,
`indexmark(firstKey/secondKey)`, and the generic `fieldBegin(TABLEOFCONTENTS)`/`fieldEnd` envelope.
It does not prove TOC parameter keys, generated-body serialization, index collation/layout, or
refresh behavior. The component keeps these bindings explicitly unverified and exposes no direct
lowering. REF-040 remains P11-owned automation.

## Validation

- Rust public TOC/index tests: `13/13 PASS`.
- Rust private sealed-plan tamper test: `1/1 PASS`.
- Focused Rust total: `14/14 PASS`.
- Private contract/source-lock/migration/validator/tamper tests: `5/5 PASS` after the final contract
  run.
- P09, P08, and P06 Python suites: `35/35`, `67/67`, and `228/228 PASS`.
- Workspace all-target/all-feature locked offline tests: `PASS`; only the pre-existing isolated
  P17 PostgreSQL qualification and two synthetic Windows credential tests remain ignored.
- Workspace Clippy with `-D warnings`: `PASS`; formatting and diff hygiene: `PASS`.

## Claim boundary

Only typed component and pinned structural source evidence is passed. `direct_hwpx`, `actual_hwpx`,
`actual_hangul`, `semantic_reopen`, `field_readback`, `reference_update`, `hancom_open`,
`save_reopen`, `render`, `automation`, and `differential` remain `false/not_run`. P09-07, P09, the
production gate, and the product remain non-green.

## Next exact task

Implement P09-08 citation/bibliography typed state for the P09-owned capability subset while keeping
automation-owned operations in P11 and every native or licensed-target claim fail-closed.
