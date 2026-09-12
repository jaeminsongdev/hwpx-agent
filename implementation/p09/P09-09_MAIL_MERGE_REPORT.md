# P09-09 mail-merge report

Decision: `COMPONENT PASS / OFFICIAL FIELD TYPE ONLY / PROVIDER AND NATIVE PARAMETERS UNVERIFIED /
GENERATION P11-OWNED / DIRECT AND TARGET NOT RUN / NON-GREEN`.

## Delivered

- Added `hwpx-agent.mail-merge/v1` for P09-owned REF-046 `ref.mailmerge_field`.
- Added complete encrypted external-source metadata, typed column schema, record count,
  row-identity manifest and mandatory access/PII policy bindings without storing row values.
- Added exact source/column selection, current field projection, generic native pair, global native
  collision checks, protection, preservation, request/build drift and sealed-plan checks.
- Added bounded strict JSON, deterministic output, redacted Debug/error surfaces, a private plan
  tamper test, versioned contract, migration, source qualification, validator and tamper tests.

## Source result

The clean pinned Hancom OWPML checkout proves the `MAILMERGE` field enum and generic
`fieldBegin`/`fieldEnd` attributes. It contains no mail-merge-specific provider schema, field
parameters, column mapping, placeholder body, preview, iteration, output or label semantics. Those
bindings remain unverified and no direct lowerer is exposed.

P09's broader work-breakdown wording is reconciled with the authoritative catalog by preserving
preview, batch-output and label-layout inventories only. Executing them is REF-047 and remains
P11-owned; this card does not promote generation.

## Validation

- Rust public mail-merge tests: `11/11 PASS`.
- Rust private sealed-plan tamper test: `1/1 PASS`.
- Focused Rust total: `12/12 PASS`.
- Private contract/source-lock/migration/validator/tamper tests: `5/5 PASS` after the final run.
- Wider Python suites: P09 `45/45 PASS`, P08 `67/67 PASS`, P06 `228/228 PASS`.
- Workspace `--all-targets --all-features --locked --offline --no-fail-fast`: `PASS`; the existing
  isolated P17 PostgreSQL qualification test and two synthetic Windows Credential Manager tests
  remain explicitly ignored.
- Workspace Clippy with `-D warnings`: `PASS`.
- `cargo fmt --all -- --check`, `git diff --check` and final contract/source-lock validators:
  `PASS`.

## Claim boundary

`native_parameter_semantics`, `provider_mapping`, `row_values`, `preview_execution`,
`batch_generation`, `label_layout_execution`, `ref_047_generate`, `direct_hwpx`, `actual_hwpx`,
`actual_hangul`, `semantic_reopen`, `field_readback`, `reference_update`, `hancom_open`,
`save_reopen`, `render`, `automation`, and `differential` remain `false/not_run`. P09-09, P09, the
production gate and the product remain non-green.

## Next exact task

Audit the remaining P09-owned REF-048 through REF-053 rows against existing typed components and
official source, then implement only the exact missing semantics before any combined target run.
