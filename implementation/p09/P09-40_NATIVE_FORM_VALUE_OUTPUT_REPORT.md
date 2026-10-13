# P09-40 managed-value output: qualified source component, not native acceptance

Date:2026-10-03. Goal ACTIVE; P09 Gate open/zero green. Sleep-time hold remains:
no Hancom/COM/native/UI execution or access-allow dialog. Read-only process
inspection found Hwp.exe count0. No new native result or batch dispatch.

## Implemented product component

New `crates/hwpx-package/src/native_form_value_output.rs` implements a separately
versioned complete-package managed-value reader, private sealed output plan,
lowerer, external output verifier and hash/count receipt. It uses the actual
public atomic FormInput API and unchanged complete v1 package reader/bindings.
The source currently compiles via explicit pending-export integration tests;
it is NOT publicly exported/routed or a dispatched native candidate.

- Five native tags: edit/checkBtn/radioBtn/comboBox/listBox. Actual package value
  changes, caller-default reset and cross-section required-radio changes are
  committed to a complete in-memory HWPX only after full atomic validation.
- Retains original v1 readback/source-state hash and derives an explicit v2
  managed-value fingerprint. No old fingerprint/expected result is overwritten.
- Whole state, flow, map, anchor, missing native identities, common properties,
  catalogs/resources/references/protection and unknown bytes remain bound.
- Every expanded output part, entry order and compression method is checked
  against exact expected bytes. Section gaps stay exact. ZIP headers/compressed
  bytes are rewritten, not promised byte-exact.
- Explicit self-closing-text expansion preserves the raw head/unknown attributes
  and matching qualified name; no unrelated normalization or native-ID injection.
- Fresh caller access/protection digest is mandatory at bind/lower/verify. Native
  protection signals, external validators, native dates, invalid XML characters,
  wrong target/source/map/policies, forged seals and bounds fail closed.
- UTF-8/XML escaping measures the complete escaped length before one reserve,
  respecting the caller part ceiling. Seek/write/span/overlap overflow checks
  return no partial package. Debug and receipts redact document values.

Ordinary tests keep artifacts in memory. Explicit qualification now emits five
actual complete source/output pairs plus a hash/count-only manifest, only into
an initially empty bounded p09-40-component-* direct child of target-build.
All11 files total167,304 bytes; directory/path/link/reparse/type/inventory/size
checks and exclusive writes prevent unbounded or original overwrites. Each
qualifier-owned temporary directory is cleaned after its independent inspection.
The earlier unbounded environment writer remains removed. Original capture bytes
stay size/SHA/link checked and unchanged. No originals were moved/deleted.

## Actual current verification

- New integration/private component:25 PASS,0 failed/ignored/filtered. Includes
  the actual private capture, capture-derived two-section six-control specimen,
  complete five-kind changes/defaults/radio, None selection, metacharacters/UTF-8/
  CR/LF/tab, empty text, unknown bytes, external output substitution, map/policy/
  source drift, revoked access, protected/read-only/disabled/noneditable targets,
  private seal mutation and preallocation/write/seek/gap limits. New fixture
  generation and directory-boundary tests supplement the earlier23-case snapshot.
- Independent Python ZIP/Expat oracle:all five actual output pairs PASS. Explicit
  target value recipes, complete expanded parts/order/compression, raw whole
  section/gap comparisons and separately derived managed-preserved fingerprints
  are checked without trusting producer target claims. Actual capture source is
  byte-exact; reset source equals the preceding actual five-kind output, and clear
  source equals its actual source. No invented native identity. Counts:

  | Case | Changed controls | Changed sections | Package parts |
  |---|---:|---:|---:|
  | actual capture |1|1|11|
  | five kinds/global radio |6|2|12|
  | empty text |1|1|12|
  | caller defaults |4|2|12|
  | clear selections |2|1|12|

- New Python tests:13 PASS, including coherent rehashes of wrong values/unknown
  attributes/children/head/closing syntax, extra/missing/order/compression/alias/
  duplicate ZIP parts, XML DTD/entities/ambiguous spans, false native promotion,
  boolean counts, invalid manifests/paths, exact compiled inventory, reset source
  linkage and privacy. Earlier12-test runs also PASS; no skips/function rewriting.
- Two fresh actual complete generator/oracle runs produce identical full results,
  not cached artifacts. Each actually runs all25 compiled Rust cases, with probe
  output separate from intact test-status protocol. Manifest SHA256
  `8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e`.
- Actual original v1 outputter still rejects the capture value transition as
  NonRepresentable. Original observed native identity remains Missing.
- Strict workspace/all-targets Clippy `-D warnings`:PASS. No lint allow/skip,
  original test changes or digest refresh.
- Entire current Rust workspace/all-targets/no-fail-fast:1,971 PASS,0 failed,
  3 existing ignored,284 suites; exit0. Includes all25 new cases. Earlier1,969/23
  and1,946/283-suite snapshots remain historical, not this current result.
- `cargo fmt --all -- --check` and `git diff --check`:PASS before report/ledger.
- P09-39 frozen current authority:PASS; includes unchanged predecessors/raw
  capsules/source pins/native artifacts. Fresh complete75,242-byte capsule
  reproduction also PASS with original SHA256
  `b5a3207f318fd038a1805908c57c1ab5fa05ec32cd148b6b8524b63bc604de92`.
  Actually reran50 original methods/146 calls/109 subtests and18 current public
  API cases, not a cached receipt. This also freshly reproduces P09-38's full
  capsule and actual current35-validator12PASS/23FAIL/original current failures.
- Ordinary full Python discovery:337 executed in509.408 seconds;10 failures and
  4 errors, exit1. All13 new tests PASS. The ten unchanged old domain-positive
  contract failures and four old-current errors (P09-37 class setup and three
  earlier source-bridge tests) are identical to the previous324-test scope.
  There is no new failure or aggregate PASS. Fresh35-validator12PASS/23FAIL and
  original predecessor failures/native histories/15/30 NOT_RUN stay intact.
- New append-only source capsule publication PASS, and fresh full --verify PASS:
  `evidence/p09-40-native-form-value-output-component.current-2020.v1.json`;
  49,546 bytes/six source pins; SHA256
  `0d9a426de31e04b27a48c63ab30e1813827b3fc73822c516d336cc64136abce8`.
  Both publication and verification actually run two new complete generators/
  oracles and the entire original P09-39 reproduction. New source capsule is
  frozen; reports/PLANS are mutable pointers. Public/native qualifications stay false.
- Post-report capsule/source/predecessor guards PASS. Six new sources and all
  prior source pins/capsules/artifacts remain exact; no shared library changes.

Hash/count-only actual capture receipt:output HWPX SHA256
`bb0a1b43fa83d6f88dbabdb63324fb7cd95546d982562d73ce76d5b54c2dca4f`;
original v1 state `7841acc0e27ca1a96ace5c21375f46e3a3936ac9efa3a03efc9aecb699a708e1`;
separate source v2 `eeec590fdc32486585756e4bd6e4261deb8eb6686a52518c2bde933b4ea65eb6`;
target v2 `9196febcd8ba546c1f05a626633dee86c04969712670332067e8cc8c07e510ee`.
All are component evidence, not actual Hancom save/reopen/render proof.

## Observed development failures and remaining limitations

Keep these failure summaries visible; no historical test/capsule was altered:

1. Initial source compile lacked the new framing helper/unused imports; repaired
   in the new source. Later fixture compile needed an explicit String tuple type.
2. Initial strict Clippy found oversized helpers, unnecessary cloning, manual
   empty strings and panic helpers; refactored the new functions/tests, using
   clone_from, fallible propagation and measured escaping. No lint suppression.
3. First22-case run:21 PASS/1 FAIL. A test changed the first section-wide protect
   attribute outside its intended form root. Fixed the new test to use the actual
   edit node span and independently assert each observed flag before rejection;
   production caller-access checks were not changed to make it pass.
4. First23-case run:22 PASS/1 FAIL. A proposed positive unknown `u:text` specimen
   is rejected by the unchanged v1 reader's local-name ambiguity check. Kept it
   as an explicit unsupported-profile negative, independently verifying the
   original UnsupportedProfile error and v2 Binding rejection. Did NOT drop,
   normalize or rename the input to pretend full unknown-profile support.
   Ordinary nonambiguous unknown attributes/children remain positive byte-exact
   preservation cases. This ambiguity support is still unimplemented.
5. The deliberately tiny ZIP output limit triggers ZipWriter's constant
   drop-finalization diagnostic. The call returns Limit/no partial output and
   its test passes; the diagnostic is retained, not hidden.
6. First25-case run:24 PASS/1 FAIL. Windows verbatim Path::join normalized the
   new traversal-negative test before validation. Constructed the actual raw
   traversal path for the test; the directory guard still rejects traversal.
   Refactored the new fixture row type for strict Clippy, with no lint suppression.
7. First generator collector rejected the compiled inventory when --nocapture
   mixed probe output into test-status lines. Switched to --show-output so all25
   original status lines and separate probe output are both strictly checked;
   no case skip/filter, status normalization or expected-count reduction.
8. The deliberate duplicate-ZIP negative fixture emits Python's duplicate-name
   warning. It is retained; the actual oracle rejects the artifact.

## Snapshot and next required work

P09-40 source/component qualification is complete and frozen under the capsule
above; this is NOT real public export, product routing, native or P09 completion.
The capsule is the source authority. Current Rust source45,592 bytes SHA256
`cab057b7d64048aadb57a7f1044701263cb8c5b5fcbd112bcab16edc78990255`;
current integration test57,800 bytes SHA256
`6c9caf391d73c2fc6e9327442d2c0156e205eaf817098265ea43b551090804de`.
The earlier unfrozen WIP snapshots are retained here as historical locations:

- source45,592 bytes SHA256 `cab057b7d64048aadb57a7f1044701263cb8c5b5fcbd112bcab16edc78990255`;
- new test49,662 bytes SHA256 `dc9ea2a2d35d6f5cb91552562730322eb0451ca304eb795319483bf532a835af`.
- shared domain lib unchanged `6f44e4baca13f0665abc6c2599bc4ab0ff559af11b02f37d7747a9334c5ccb85`;
  shared package lib unchanged `95ba3752b2b3c6b2e1bd1879cdb05aabaef1e7ca0ca91e70b2843b2cbd0a247b`.

Next:real public export with exact source archives/dependency qualification; actual
product routing and all genuinely changed dependency-ready native cases. Do
not stop at a pending-export component or dispatch source-included candidates.
Native permission/resave/render and broader notes/fields/state/default/type/
protection/differential/Gates remain open. No P10 before authoritative P09 Gate.
After explicit user resume only, native work is one whole sequential batch.

Read-only follow-up inspection confirms the current product CLI still exposes
only create-vs0 and has no form input route. Do not label the compiled component
as product routing. A namespaced additive public module can preserve unchanged
pending-test bodies without introducing conflicting root glob exports; qualify
that actual production/public consumer before any native fixture dispatch.
