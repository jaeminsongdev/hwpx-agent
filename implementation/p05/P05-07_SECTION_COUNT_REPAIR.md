# P05-07 header section-count repair

- Date: 2026-09-05
- Review: STRICT / HIGH; recommended reasoning `max`.
- State: `core_repair_current_and_independent_full_pass_actual_2020_pending`.
- Parent implementation: `9360c47fc6c8958f6f9a16b954491579d774342d`.
- Repair implementation checkpoint: `e82cf95abb6d4109e81e6ecf7b450de0f1d4b55a`.
- Full product and P05 Gate are not complete.

## Finding and evidence

The v2 multi-section fixture still has `hh:head/@secCnt="1"`, despite containing two section
parts and two ordered linear spine entries. Its generator copied the one-section VS-0 header
unchanged; its inspector validated both body parts but never correlated the declared header count.
This is a confirmed generator/admission defect, not evidence of a PC or licensing fault.

Attempt 17 opened this v2 fixture in the exact licensed Hangul 2020 and read a text digest that
matches the first section marker alone. The stale count is consistent with that symptom, but
causation and actual-Hangul recovery require a v3 run; neither is claimed from pure tests.
See `P05-07_ATTEMPT17_DIAGNOSTIC.md` for the preserved actual trace.

The locally locked official machine-readable KS X 6101 Appendix C declares `secCnt` as required
`xs:nonNegativeInteger`. Source digest was rechecked as
`c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`; extracted record is
`ks-x-6101-machine-content-20260901:xsd:000051`. That 2024 source is structural documentation,
not 2020 runtime proof. The namespace and original one-section header come from the exact
current-2020 VS-0 template, which remains unchanged.

## Implementation

The product section/column module now offers bounded header-count reading, header-aware sequence
admission and a preserving count lowerer with an expected-prior-count precondition. The lowerer
replaces only the value span and returns a digest-bound receipt; the source is immutable.
`section_columns_section_count_mismatch` is an additive stable error code. No dependency, public
MCP schema, security-prompt behavior, Registry value or predecessor template changed.

The P05-07 generator updates the count before creating a new package; its inspector combines
header-aware sequence admission with its existing exact spine, graph closure, text and geometry
checks. The old header-free sequence API remains a value-level API, explicitly not whole-package
validation. The new count reader similarly does not claim complete header/style validation.

## Validation

| Check | Current result |
|---|---|
| Regression before repair | Fails at generated header: actual 1, expected 2 |
| Section/column tests | 14/14 pass |
| New header-count tests | 8/8 pass |
| Target fixture tests | 7/7 pass, including stale-header rejection and deterministic/no-overwrite build |
| Workspace all-target/all-feature Clippy | PASS; subsequent CI Clippy also passes |
| V3 build and product inspection | PASS: two sections, one boundary, unchanged expected text digest |
| Independent ZIP part comparison | 12 parts in both; only header.xml differs, exactly secCnt 1 to 2 |
| Old v2 fixture through repaired inspector | Correctly rejected with SectionCountMismatch |
| Current checkout full CI | PASS, five terminal lanes, session 5232 exit 0 |
| Offline Linux package all-target tests and Clippy | PASS, exact Rust 1.96.0 image; network disabled and source/registry read-only |
| Exact clean-checkout/full | PASS at e82cf95, five terminal lanes, session 68068 exit 0 |
| Actual Hangul 2020 v3 readback/PDF/visual Gate | Attempt 18 timed out at open_input; no save/readback/PDF acceptance |

Negative coverage includes root/attribute namespace spoofing, missing/duplicate counts, child
decoys, DTD/entity declarations, multiple roots, invalid/oversized numbers, count disagreement,
empty/invalid sequences, prior-count conflicts and input/output/element/count bounds. Positive
preservation checks cover BOM, CRLF, single quotes, numeric character references, Korean text,
comments and repeatable receipts without altering any byte outside the selected value span.

The first Linux invocation stopped before compilation when rustup tried to update requested
components in a read-only root. It was not accepted. The successful invocation explicitly selected
the already-installed `1.96.0-x86_64-unknown-linux-gnu` toolchain in image
`sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`, without network or
relaxing source/registry protection. It ran `cargo test --locked --offline -p hwpx-package
--all-targets -j 4` and package all-target Clippy with warnings denied. Its temporary build/cache
were container-local and removed with that container. This is package portability evidence,
not a whole-workspace Linux or actual-Hangul claim.

The exact detached checkout is `D:\개발\hwpx-agent-audit-p05-count-e82cf95`. Only the four
hash-pinned P10 diagnostic JSON records were copied into its ignored evidence paths; tracked Git
status was clean before the run. Its live full-CI log is `artifacts/p05-count-repair/full-ci.log`.
The current run started against the same implementation bytes before checkpointing; it is not an
independent-checkout receipt. The current run terminated with all five lanes passed: linux-core
17.412 s, windows-worker 61.095 s, widget 5.766 s, docs 1370.430 s and security 23.220 s. Its
security report is `implementation/p01/evidence/security-runs/3f6dece28e8b4072829e5899261ebfcf/report.json`:
nine checks exit 0, no failed check or forbidden license. Existing duplicate-crate warnings remain
warnings, not silently removed. The independent run also terminated exit 0 with all five lanes
passed: linux-core 55.415 s, windows-worker 67.547 s, widget 6.470 s, docs 1346.156 s and security
14.233 s. Its tracked checkout remains clean. Durable log SHA-256 is
`35fdafdca5a6fef5055c25d05b4cc8cb4bf0cc87241aaea1a8c97c71fa95990c`.
The independent security run `b6c4d8947cee48dc984526bfaa5f6a7a` has nine zero-exit checks, no failed
check or forbidden license. These full runs qualify the count-repair checkpoint only; they do not
qualify later P16 safety edits or supply missing actual Hangul acceptance.

## Fresh disposable v3 target

- Directory: `fixtures/target-build/p05-07-current-2020-20260905-v3/` (Git-ignored).
- Input: `p05-07-section-columns-input.hwpx`, 8,842 bytes.
- SHA-256: `dc2d385ecdc60a396f5740d604b8ce379f25733c87bf98ed3e3baa32291e49a5`.
- Expected normalized text SHA-256 remains
  `92d2179169f1102d256589c2ca90b8422405076927d91c6e5ba2e91f28381d2f`.
- Existing v2 fixture and all attempts are preserved. V3 attempt 18 launched on 2026-09-05
  after the user explicitly offered immediate access approval. The unchanged wrapper uses a
  600-second watchdog and new attempt-18 output/trace/PDF names; expected text is unchanged.
  Progress stopped after preflight/com_create pass and open_input running. The 600-second watchdog
  terminated the worker and one owned Hwp process; input is unchanged, no output/PDF, no residual
  Hwp process. See `P05-07_ATTEMPT18_DIAGNOSTIC.md`; this is not actual acceptance.

## Next acceptance

Finish the software verification without promoting it into actual acceptance. In a user-present
approval session, run the unchanged bounded 2020 wrapper against v3 using new output/trace/PDF
names. Require both section markers before saving, then verify saved/reopened semantics, exact
PDF geometry/text and every rendered page. Do not change expected text to the observed v2 result.
If actual readback still fails, investigate extraction/import with focused evidence, not blind retries.
