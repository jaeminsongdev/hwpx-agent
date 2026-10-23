# Literal replacement of mixed source text

## Candidate scope

lower_literal_text_atom_candidate produces a source-literal-replacement-candidate/v2 from actual
mapped body/note literal matches. It admits Text atoms before or after original tabs/lineBreaks,
unlike the unchanged plain-only v1 compiler. It neither flattens controls nor admits control editing.

The exact original's call-local Form reconstruction proof is required. The compiler shares the
original NFC provenance/exactness/contiguity selector and rejects overlapping original contributions.
Matches are grouped by source text element, atom and scalar range. FirstOriginalRunRetainAllRuns
places replacement in the first original group and deletes only later selected text ranges.
Any selected control atom rejects the whole candidate, including a literal query containing tab/LF.
The existing value policy rejects control/noncharacter replacement text; regex is not admitted.

The original field collector supplies merged field intervals. Cached field content remains rejected
even when editable=1. Observed table/cell/size/ancestor protection is indexed once per changed part.
The receipt does not claim complete protection, hidden/MEMO replacement or Native semantics.
No per-match package/Form reconstruction, patch or whole-output import is introduced.

## Output and preservation

All ranges for a text element use one ReplaceTextAtomScalarRanges intent. The original patch/ID/
preservation/writer prefix is extracted and shared with v1 without changing its checks or profile.
The output Form and fields are imported once per candidate. Each expected TextSpan is compared by
typed value, a domain-separated streaming digest and text byte count. That digest binds style-ref
presence/value, atom order/count, text lengths/values, tab width/leader/type and lineBreak kinds.
Complete text deletion removes only empty Text atoms from the expected reader model, not source tags.

Each slot is the byte interval between whole controls inside a text element. Slot numbers remain
stable when empty Text atoms disappear and parsed atom indices shift. Source/output XML outside
selected Text atom slots, including exact control XML/internal whitespace, is compared byte-for-byte.
Other package parts remain exact through the shared patch/writer checks.

Independent readback deliberately claims outside_selected_text_atoms_exact, not byte comparison of
every unselected scalar inside an edited atom. The latter preservation follows the separately
qualified scalar patch algorithm. Receipt flags output_text_span_values_verified and
original_control_bytes_preserved are true; control_atom_replacement_qualified,
field_cached_content_edit_qualified and full_protection_native_or_execution_authority remain false.
Text/slot plans stay private; receipts expose original anchors, digests, counts and byte lengths only.

Original range-count/value/escaped-output limits, search result and receipt byte limits, matched
occurrence caps and writer output bounds apply. Semantic no-op ranges retain their original entity
spelling; an entirely unchanged request returns NoChange. Limits fail rather than truncate a success.

## Current stored service

prepare_literal_text_atom_candidate returns a borrowed PreparedStoredLiteralTextAtomCandidate with
stored-literal-search-candidate/v2. It checks current document.write and the original scope/head/ACL/
quarantine/AEAD source and whole Form proof. Output source digest and final preparation head are bound.
The existing source read/reconstruction functions and original v1 access checks are reused; all five
preparation/fresh/verify/delivery/denied-route method bodies are compared with v1 outside typed output,
source ownership spelling and additional closed v2 flags.

Retained verify/delivery recheck current access and source and writer integrity, without rerunning
the query or candidate lowering. The final consumer head check remains inside the writer callback.
Receipts/copies are not access authority. There is no caller-provided trusted-output trait or unchecked
byte accessor. require_current_product_route still denies after fresh verification.

No ingest, source overwrite, durable idempotency key claim, revision commit/CAS, CLI/server dispatcher,
executable or publication route is added. The v2 candidate now reuses the existing private Borrowed/
Owned source enum; its internal ownership adapter moves the prepared output/receipt and boxes the
source without cloning or ownership-driven reimport. The required initial import and fresh whole
Form reconstruction remain. Its [strict v2 JSON adapter](p09-literal-replacement-product-request-v2.md)
uses the same current-access/delivery bodies. Existing v1 JSON schema and mixed-leaf rejection remain.

## Verification

Components075 passes 12 new v2 core and 10 affected v1 core cases:22 total,484 fresh/final484,
no diagnostics and terminal/empty/closed Jobs. Exact inverse checks preserve the original v1
compiler/provenance checks, writer/ID/preservation prefix and readback bodies outside extraction.
Tests cover mixed matches/deletions, cross-run styles, three-run Hangul NFC, reordered/partial NFC
rejection, original scope/case/whole-word, no-op entities, field/protection/control rejection,4096
range and response/writer caps, redaction and one protection map with2N visits for200 matches.

Stored Components076 fails compilation on one new test's unqualified ArtifactPermission name,
with zero tests executed. Recovery077 changes only that test reference to the fully qualified
artifact_service::ArtifactPermission and passes six new stored cases,489 fresh/final489, with cleanup.
The original failure stays immutable and all production/source/protection policies remain unchanged.
The known search_review_fixture package helper warning remains disclosed.

Stored tests cover actual cross-run bytes/control preservation, write scope, foreign document,
ACL revoke/regrant, quarantine/AEAD, preparation/verify/final-consumer head races, scope/digests and
invalid control/field/mode/match/response/writer bounds. V1 rejects the same mixed source in the test.
These six passes plus the 22 retained core passes are28 current cases; core is not rerun for storage.
Other scalar/stored/product suites and the official249 queue are not replayed.

Core overall92.703s, commands26.547/4.187s and tests3.51/2.77s; system CPU at most25.71%, available
RAM at least27.6842%, peak Job private5.0323%. Stored recovery overall186.281s, command121.234s and
tests8.33s; system CPU at most29.40%, available RAM at least28.4297%, peak Job private3.0408%.
All owned Jobs end active0/empty/handle closed. One core, BelowNormal, CPU cap6.25%, private cap8%/
stop7%, RAM/commit95% and input checks remain. These are execution observations, not a benchmark
or proof that PC freezes are fixed.

## Remaining product work

Variable regex capture expansions use the same protected compiler through a separate
[regex source profile](p09-source-selector-regex-replacement-v1.md). Fixed literal behavior and the None
compiler path are preserved; this does not add regex support to existing literal product schemas.
The separate [regex product profile](p09-regex-replacement-product-request-v1.md) qualifies current storage
and strict JSON for that candidate without changing these literal meanings.

Source ownership handoff and strict v2 product JSON preparation are qualified separately in
[the v2 product request profile](p09-literal-replacement-product-request-v2.md), including 25 current
product/affected cases. This does not replay or relabel the source/patch results above.
Explicit hidden/MEMO source candidates and borrowed current storage are qualified separately in
[the v3 source profile](p09-source-review-literal-output-v3.md). Its
[strict v3 JSON/owned adapter](p09-review-literal-product-request-v3.md) is qualified separately;
existing v1/v2 semantics and field/control guards are not widened.
Full SearchScopeSelector, field/newline replacement, complete protection, target match_set/
semantic_diff/reopen, dispatcher/DB/CAS/execution/publication and Native remain unqualified.
Source API v12 is incomplete/four unresolved/null report/exit3. Queue158/249,91 remaining, next165,
fixed CROSSREF8 NOT_RUN, Native011 unapproved/unexecuted, P09/A12/A13 OPEN, P10 not started and
the full P09–P20 goal ACTIVE remain unchanged.
