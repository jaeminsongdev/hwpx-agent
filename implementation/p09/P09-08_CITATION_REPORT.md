# P09-08 citation report

Decision: `COMPONENT PASS / OFFICIAL STRUCTURE PARTIALLY QUALIFIED /
UNVERIFIED BIBLIOGRAPHY FORMAT AND CITATION PARAMETERS / DIRECT AND TARGET NOT RUN / NON-GREEN`.

## Delivered

- Added `hwpx-agent.citation/v1` for the P09-owned REF-044 `ref.citation_insert` capability.
- Added complete bibliography catalog/provider/source snapshots, ordered multi-source citation
  references, locator/prefix/suffix/suppress-author options, visible cache and generic native field
  envelope state.
- Added selected-source projection semantics, global native ID/name collision checks, protection,
  preservation, request/build drift, strict JSON, finite limits and redacted Debug.
- Added a sealed plan/private tamper test, versioned contract, migration, pinned-source
  qualification, validator and contract tamper tests.

## Source result

The clean pinned Hancom OWPML checkout proves `CITATION` and `BIBLIOGRAPHY` field enum values, the
generic `fieldBegin`/`fieldEnd` envelope, and the package path/id/media-type used to preserve an
opaque bibliography part. `_ReadBibliography()` is a stub and `_WriteBibliography()` copies an
already decompressed part. No source proves bibliography record XML, provider mapping, citation
parameter keys, visible-body generation or refresh semantics. The component keeps these bindings
unverified and exposes no direct lowerer. REF-043 and REF-045 remain P11-owned.

## Validation

- Rust public citation tests: `11/11 PASS`.
- Rust private sealed-plan tamper test: `1/1 PASS`.
- Focused Rust total: `12/12 PASS`.
- Private contract/source-lock/migration/validator/tamper tests: `5/5 PASS` after the final contract
  run.
- P09/P08/P06 Python suites: `40/40`, `67/67`, and `228/228 PASS`.
- Workspace all-target/all-feature locked offline tests: `PASS`; the existing isolated P17
  PostgreSQL qualification test and two synthetic Windows credential tests remain `ignored`.
- Workspace all-target/all-feature Clippy with `-D warnings`: `PASS`.
- `cargo fmt --check`, `git diff --check`, and the final source-lock/contract reruns: `PASS`.

## Claim boundary

Only typed component and pinned structural source evidence is passed. `direct_hwpx`, `actual_hwpx`,
`actual_hangul`, `semantic_reopen`, `field_readback`, `reference_update`, `hancom_open`,
`save_reopen`, `render`, `automation`, and `differential` remain `false/not_run`. P09-08, P09, the
production gate, and the product remain non-green.

## Next exact task

Implement P09-09 mail-merge field insertion for the P09-owned REF-046 subset while keeping
REF-047 generation in P11 and native provider semantics fail-closed.
