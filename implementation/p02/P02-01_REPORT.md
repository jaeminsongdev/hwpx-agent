# P02-01 SourceRecord Contract Report

- Completed: 2026-09-01
- Audited source commit: `52228e0fd1e47e91c45b34f16a11c5089a53cc20`
- Task state: `pass_current_pc_local`
- Review: `STRICT / xhigh`, blocker/major/minor `0/0/0`

## Delivered contract

- Draft 2020-12 `SourceRecordV1` schema with immutable source-lock ID, source ID/SHA-256, source kind, kind-compatible locator, original name/description, ordered parameter metadata, structured availability and deterministic extractor identity.
- Strict source-kind/locator rules for help/WebHWP, PDF, XSD, automation metadata and runtime probes.
- Runtime observations require an exact target profile and exact version; synthetic runtime metadata remains `current_pc_candidate` and is not represented as actual 한글 evidence.
- Five synthetic valid samples cover help, PDF, XSD, action-table metadata and runtime metadata.
- Ten negative cases cover missing/malformed hash, unknown property, invalid source-kind locator, ambiguous page locator, runtime target omission, missing parameter direction, reversed build range and non-contiguous parameter ordinals.
- Deterministic Rust and TypeScript generated models plus drift checking. P01's immutable foundation catalog remains byte-identical at SHA-256 `0730f6bee97232dd8ffbd26b6723321f3864852db82a593019f3ecdb14129aed`.
- Additive `schema-catalog-v2.json` is separately locked at SHA-256 `21732da04009162452492026198654dd895d2537f69569788e44f8e2323605f5`; the migration note requires the next catalog/schema version for later additive or breaking work.

## Validation

- Current working repository full bootstrap: 5/5 lanes passed.
- Official Rust 1.96.0 Linux container with read-only source mount: linux-core passed.
- Clean clone at `52228e0`: full bootstrap 5/5 passed and post-run Git status changes 0.
- Rust tests: 11 passed, including generated `SourceRecordV1` deserialization.
- TypeScript tests: 4 passed, including generated catalog/model shape.
- SourceRecord validator: valid samples 5/5, negative cases 10/10 rejected, errors 0.
- Format, Clippy `-D warnings`, schema compile, generated drift and v1/v2 baseline locks passed.
- Secret findings, `unsafe` Rust and SourceRecord raw execution surface each 0.
- Original design ZIP still matches SHA-256 `dfcb1ff9de18ff11d7cb158f499031ac702937a33d19e8ff02125bb5f1909446`.

## Boundary

The schema is authoritative for nested locator, availability and parameter validation. Generated language models provide deterministic transport types; extractors must still pass their output through the schema and semantic validator before publication. P02-01 did not read or redistribute an official binary source, invoke 한글/COM/UI, access a user document, or qualify another PC/version.

## Failed fixture retained

The first FULL run failed on two new Clippy warnings in the generator. The helper was corrected to borrow catalog entries and remove a duplicate match arm; the complete validation was rerun from the start. All ten SourceRecord negative cases remain executable in `tools/p02/validate_source_records.py`.

## Next exact task

Implement `P02-02 Help extractor` as a read-only adapter over an approved source-lock entry. Preserve source SHA-256 and original locator, emit deterministic `SourceRecordV1` records, reject source-lock mismatch and unsupported input, and never modify source material. Recommended reasoning effort: `xhigh`; P02 final Gate: `max`. No user local operation is required at task start.
