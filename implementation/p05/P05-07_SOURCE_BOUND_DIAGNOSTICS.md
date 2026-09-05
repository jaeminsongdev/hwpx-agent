# P05-07 source-bound saved-document diagnostics

- Date: 2026-09-05; parent checkpoint `361068e` (orientation implementation `9f493a5`).
- Implementation worktree: `D:\개발\hwpx-agent-work-p05-diagnostics`.
- Scope: fixed synthetic P05-07 fixture, current licensed Hangul 2020 `11.0.0.9136` x86 only.
- Review: HIGH / STRICT. This is diagnostic implementation, not P05-07 or normalization acceptance.

## Implementation

The existing fixture example has an additional read-only command:

```text
cargo run --locked --offline -p hwpx-package --example p05_07_section_columns_target_fixture -- diagnose <source.hwpx> <saved.hwpx> <trace.json> <trace-sha256>
```

It emits `hwpx-agent.p05-07-source-bound-diagnostic/v1` JSON on stdout. Differences return exit 1
after the diagnostic JSON; malformed inputs/trace are rejected without a comparison report. Exit 0
means only that all fixed-fixture semantic comparisons matched. Every report still states
`overall_acceptance=not_granted_diagnostic_only`, no independent execution attestation, no PDF or
visual verification, and no verified logical-identity remap. This CLI cannot publish a revision.

The `build` and strict `inspect` modes, package readers, full `ColumnDefinition` equality, current
page expectations and existing preservation tests remain unchanged. The new private support module
does not add a public LLM/MCP operation or normalization permission.

### Input and evidence boundary

- Package reads are capped at 8 MiB and trace reads at 128 KiB, including a bounded read after the
  metadata check. Empty, oversized, symlink/nonregular and changing-size inputs reject.
- Both packages undergo bounded ZIP/closed graph admission, exact three-part spine ordering,
  linear section checks, graph/entry closure and exact two-section header count correlation.
- The trace's caller-supplied SHA-256 must match. Closed typed JSON rejects unknown or duplicate
  fields, wrong types and missing required fields, including explicit nullable error fields.
- Package/text digests, current build/executable profile, all readback phases, privacy flags and
  normal terminal watchdog state must be consistent. An ordinary local JSON claim is explicitly
  not independent proof that an actual run occurred. PDF claims are not PDF-content verification.
- Output contains digests, bounded ordinals and comparison facts, not document text, backend IDs,
  raw XML, arbitrary paths or private exception strings.

### Independent comparison dimensions

Page equality between source and saved output is distinct from matching the requested target.
Two equally incorrect pages do not pass. Typed column interpretation in the requested target body
frame is distinct from column admission at each document's actual page body width. This permits
reporting ID removal even when a wrong orientation makes custom widths invalid; it never labels
those widths valid for the actual page.

Column values excluding IDs are a labeled diagnostic dimension only. Target IDs and source/saved
ID equality remain separate required comparisons. Missing/ambiguous column interpretation yields
no comparable removal count (`null`), not a false claim of zero removals. Two removed identifiers
remain two observations; the empty string never becomes a shared identity or a remap key.

## Validation and preserved failures

The first new diagnostic implementation had two admission gaps: optional error fields could be
omitted from the trace, and comparing two equally modified empty IDs did not also check fixed
target IDs. Two behavioral regressions failed before hardening and passed after repair. Their
failed log remains intact. Twelve new diagnostic tests now pass, alongside eleven pre-existing
fixture tests. No existing test/assertion, corpus pin, timeout or runtime admission was relaxed.

All package targets: **205 passed, zero ignored**. All-target/all-feature Clippy with warnings denied
passed. Four narrow `struct_excessive_bools` expectations document independent comparison fields
and the pre-existing external trace/watchdog wire shape; they do not suppress test failures,
trace checks, parser checks or an entire lint group. Both `serde` and `serde_json` are already pinned
workspace dependencies; only dev-dependency edges were added, with no new version or package.

| Log under this worktree's artifacts/p05-source-diagnostics | SHA-256 |
|---|---|
| tests-before-hardening.log | ffc95eff420f7140f425f340be3a2d7f2928bdf096df223f08667bff0b415c07 |
| package-tests-final.log | 66ffee6ad4aaa59f7efa188f075b2c70d9a3c84b9f11d7427000455502df3ec6 |
| clippy-final-02.log | f4777bfa0eaab2f4ae154222e9e06ca8d1a4c5c9bfc8175c06dab28c76998205 |
| attempt21-diagnostic.json | 094fcc02bb6b8bfe86c904cd1663baf0c3b4d87d5952d47bf2d7365cd275679f |
| linux-offline.log (first invocation failed before compilation) | de6374aa23b5d25e03466dc0d2d4604fcc04569ea4bb91c005840ca1e12ea913 |
| linux-offline-retry02.log | 7fb4a1466e869fbdf0fa1401eb9ff828277eddb64f1367da1624d5f9850527af |

The full package test and Clippy session 22076 is terminal exit 0. Initial package session 84128
also terminated exit 0 at 203 tests before two further regressions were added.

Actual offline Linux: **205/205 tests and Clippy PASS**, session 96358 terminal exit 0. The existing
pinned Rust image `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f` ran
with network disabled, read-only source/registry/root, dropped capabilities and bounded temporary
build storage. The owned container is absent afterward. The first login-shell invocation could not
resolve Cargo and exited 127 before compilation. Its failed log is preserved; using the image's
existing PATH through a non-login shell resolved the invocation. No image, toolchain, code or test
was changed to obtain that retry result.

## Actual saved attempt21: diagnostic failure retained

The unchanged main-checkout source/output/trace were read by absolute path and their SHA-256
rechecked afterward against `P05-07_ATTEMPT21_DIAGNOSTIC.md`. No Hancom launch or UI input occurred.
The diagnostic returned exit 1 as required, with these independent observations:

- Both source and saved page setups match each other but not the requested landscape target.
- In section 1 (zero-based), custom widths fail admission at the actual portrait body width in
  both files. The intended target frame can still interpret the unchanged column values.
- Both sections retain their compared column values and text, but each loses its nonempty backend
  column identifier. Neither identifier is marked preserved or remapped.

This also distinguishes a pre-existing malformed target layout from the additional saved-ID
normalization. The old failed output and all expectations remain untouched.

## Open qualification work

Actual offline Linux tests/Clippy pass; FULL audits of this new implementation remain required
before implementation closure. Do not apply the predecessor orientation audit's PASS to this code.
The separate current/independent orientation FULL audits remain identified in
`P05-07_ORIENTATION_AUDIT_STATUS.md` in main. Main's bounded ledger is authoritative; this
implementation worktree's inherited ledger is historical until integration.

Actual corrected landscape output, column identity preservation/rebinding, dense column flow,
balancing, PDF/visual checks and the wider P05/P12 requirements remain open. No user click is
pending; a meaningful corrected fixture and fresh user-present request precede another actual run.
Recommended reasoning: `max` for normalization/preservation and final Gates.
