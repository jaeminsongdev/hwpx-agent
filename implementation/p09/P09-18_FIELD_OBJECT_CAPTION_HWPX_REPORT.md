# P09-18 object-bound caption number composition report

Date: 2026-10-02. Base: `1f8cd23da15d2e517e0e5640eae2bffe2c19af3f`.
Profile: `hwpx-agent.field-object-caption-hwpx.hwpml-2011-digit/v1`.

## Implemented

- Added the typed native-object selector, caption scoped reader, sealed composition
  builder and preserving lowerer in `field_object_caption_hwpx.rs`.
- Reused the existing field engine and P09-16 numeric adapter without editing them.
- Bound full source section/object/caption, selector, state/flow/map and nested plans;
  preserved every byte outside the verified field edit and relifted target state.
- Added public package exports. No public LLM action or arbitrary XML route was added.
- Added a separate source contract/qualification with official OWPML file locks,
  inherited reference source locks, implementation locks and exact claim boundaries.

## Focused evidence

Caption public tests: **8/8 PASS**. Private sealed-plan tamper test: **1/1 PASS**.
Package all-target/all-feature locked offline Clippy with `-D warnings`: **PASS**.

Checks cover all three number kinds; seven additional picture/shape variants;
deterministic retries; insert reversal to exact original bytes; update-only `num`;
wrong kind, source, selector, flow/map drift; missing/duplicate/locked/shadowed scopes;
complete multiline caption maps; opaque preservation; redacted Debug and finite limits.
Private test corrupts selected native ID, source-section hash and caption hash.

Fixtures are **synthetic object shells**. The word "object" in a test name does not
assert a complete native object, package or real application evidence. No new COM/UI
run occurred. P09-17's 2/3/4 -> 0/0/0 failure remains preserved, not superseded by
this static pass. Caption association is an implemented candidate correction;
causal confirmation requires fresh application evidence.

Reproduce:

```powershell
cargo test -p hwpx-package --test field_object_caption_hwpx --all-features --locked --offline
cargo test -p hwpx-package --lib sealed_composition_target_and_source_hash_tampering_are_rejected --all-features --locked --offline
cargo clippy -p hwpx-package --all-targets --all-features --locked --offline -- -D warnings
py -3 tools/p09/validate_field_object_caption_hwpx_contract.py
py -3 -m unittest tools.p09.tests.test_field_object_caption_hwpx_contract -q
```

## Same-turn regression checks

New contract validator: PASS with 4 reference-source locks, 6 implementation locks
and 15 official-model locks. Contract regression tests: **8/8 PASS**, including
claim/profile weakening, boolean/integer confusion, linked file/ancestor rejection,
duplicate JSON, oversized/missing files, export removal and source drift.

Full P09 Python suite: **110/110 PASS**, with no skipped test. Rust workspace
all-target/all-feature locked offline tests: **PASS** (263 result summaries;
ignored external checks remain ignored, not application evidence). Workspace
Clippy with the same flags and `-D warnings`: **PASS**. `cargo fmt --all -- --check`
and `git diff --check`: **PASS**. Existing numeric adapter, P09 aggregate contract
and frozen P17 source-v48 contract: **PASS**. No HWP process was running at inspection.

The P08 asset-pipeline source validator still reports `implementation_digest`.
Current shared `lib.rs` hash is
`9b1a0b883e0dfa9f99a61762d21d3bf03c98569289e2aba9b36b6d69ae2311d8`.
Removing only both P09 module/export blocks in memory reproduces pinned P08 hash
`a22f9f73f04e17ac3439022fcf6aaa0fb5f5ddb02d48257d10998bd01bdf2e12`.
This diagnostic changed no source bytes and does not turn P08's live failure into PASS.

## Gate status and remaining work

`green_rows=0`, `p09_complete=false`, `product_complete=false`. P09-11 remains
35 unit + 11 static integration with 7 P11-deferred rows. Application-owned sequence
derivation, complete actual-object fixtures, exact-target save/reopen, render and
direct/automation differential remain NOT_RUN for the new adapter.

The source-bound P08 aggregate hold on shared `lib.rs` remains. This adapter adds
another independent P09 module/export to that shared file. Historical P08 receipts
and source locks must not be overwritten to hide this new source identity.

Next: create a complete-object caption-number campaign, then stop before any new
access-allow validation. P10 remains held until genuine P09 Gate closure.
