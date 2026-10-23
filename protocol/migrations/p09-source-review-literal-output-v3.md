# Explicit review body literal replacement v3

The source candidate `hwpx-agent.source-literal-replacement-candidate/v3` extends literal
replacement to actual hidden explanation and MEMO payload paragraphs under two explicit
Boolean policies. Core, current stored-service and [strict v3 product preparation](p09-review-literal-product-request-v3.md)
boundaries are verified; executable storage transactions and Native remain pending.

## Source policy and field boundaries

`lower_review_literal_candidate` requires the original whole Form reconstruction proof and
`SourceReviewTextPolicy { include_hidden_explanations, include_memo_bodies }`. The existing
review mapper and search projection are reused once. Scope is checked against the whole
admitted corpus before exclusions; excluded matches do not consume result limits. Match
regions distinguish body_and_notes, hidden_explanation and memo_body. These are source-file
regions, not the application's current visibility or resolution state.

The write context permits only the exact direct subList payload of an admitted, paired MEMO
fieldBegin. Its own field interval is split around that payload before merging all intervals.
Other and enclosing field intervals stay intact, so the exception cannot bypass an outer
field or permit hidden text in cached results. Bodyless MEMO has no exception. editable=0/1
does not grant cache writes. Wrapper, parameters, metaTag and cached sibling text remain outside
the permitted payload. Malformed or nested field/review envelopes fail even when excluded.

The original NFC provenance, contiguous selection, overlap, run policy, mixed-control rejection,
finite limits and per-part protection map remain. One batch produces one patch transaction and
one output Form import. Output fields and review bodies are imported once against that output;
no per-match package or Form reconstruction is introduced. Original TextSpan readback and exact
bytes outside selected atom slots remain shared with v2. Preservation of unselected scalars
inside an edited atom follows the qualified scalar patch, not a broader independent readback claim.

Receipts bind policy, source/output review inventories, review-search request, match regions and
permitted MEMO payload count. memo_payload_not_cached_result_verified is true; cached-field editing,
control-atom replacement, complete protection, native author/visibility/resolution and execution
authority remain false. Existing v1/v2 JSON rejects unsupported review policy rather than ignoring it.

## Current stored service

`prepare_review_literal_candidate` returns a borrowed candidate with
`hwpx-agent.stored-literal-search-candidate/v3`. document.write, original provider scope/head/ACL,
quarantine/AEAD and fresh whole Form proof remain mandatory. Original preparation, fresh verification,
writer integrity and final-consumer head boundaries are preserved outside typed output/policy and
closed v3 receipt checks. Retained delivery does not repeat query, lowering or review projection.
The source owner enum is reused; the private v3 owned adapter moves output/receipt and boxes the
source without cloning or ownership-driven reimport. Required initial and fresh imports remain.

No unchecked byte accessor, ingest, source overwrite, durable key claim, revision commit/CAS,
CLI/server dispatcher, executable or publication route is added. require_current_product_route
continues to deny after fresh verification. Receipts are not authority.

## Verification and focused target

Components081 passes 12 new core cases and 20 affected v2/review-search cases:32 total,495
fresh/final495, no diagnostics, cleanup true. Core elapsed93.359s; maximum system CPU17.99%,
minimum available RAM29.2988%. Original v2 compiler/readback and review projection checks remain.

Stored components082 stops at the unchanged300s command deadline with cleanup true and no recorded
test results. Missing results are not proof of zero execution and are never promoted to PASS.
Focused083 fails before Cargo on a missing-result-field KeyError. Focused084 fails before Cargo
on an incorrect exact target-text expectation; the actual target has no extra blank line. All
three immutable failure records remain. Product code and the six stored test bodies were not
changed to obtain the later pass.

Focused085 passes the same six stored cases in a dedicated review_literal_stored integration target.
The original StoredFixture new/provider source is shared at the original lexical scope; reconstructing
the old root and module yields the exact previous source. Existing legacy test bodies remain unchanged.
The legacy form_stored_provider target passes cargo check only; its tests are not executed.
The preexisting unused fixture package warning remains in that check; the dedicated six have no diagnostics.
32 retained core plus6 stored equals38 distinct component cases, not38 newly executed recovery tests.

Focused elapsed160.188s, six-case command81.281s/test0.32s, legacy check12.578s;502 fresh/final502.
Maximum system CPU31.05%, minimum available RAM26.7908%, peak Job private5.0788% of physical RAM.
Both Jobs end active0/empty/handle closed. One core, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95%, command300s and guard600s remain. Bounded observations retain only phase, expected test
names/status and output lengths/hashes, not raw logs. These are run observations, not a benchmark
or proof that PC freezes are fixed. Existing core32 and the official249 queue are not replayed.

Evidence: implementation/p09/evidence/p09-361-review-literal-components081.v1.json and
implementation/p09/evidence/p09-361-stored-review-literal-focused085.v1.json.

## Remaining work

The separate [regex capture source profile](p09-source-selector-regex-replacement-v1.md) reuses this exact
MEMO payload/ancestor-field protection and review readback with per-match expansions. Its current storage/
strict JSON connection is qualified in [the regex product profile](p09-regex-replacement-product-request-v1.md);
existing literal requests retain their original meaning.

Strict v3 product JSON and owned-source handoff are qualified separately in
[the v3 product profile](p09-review-literal-product-request-v3.md), with35 product/affected passes.
Exact document/section/selection/node_set windows now feed this qualified compiler through the separate
[selector candidate and stored profile](p09-stored-review-selector-candidates-v1.md). That outer candidate
retains the v3 body receipt and never expands partial windows into whole paragraphs. Its separate strict
v4 request is qualified in [the selector product profile](p09-review-selector-product-requests.md).
Existing v1/v2/v3 semantics stay separate.
Full SearchScopeSelector, field/newline replacement, complete protection, target match_set/
semantic_diff/reopen, dispatcher/DB/CAS/execution/publication and Native remain unqualified.
Source API v12 is incomplete/four unresolved/null report/exit3. Queue158/249,91 remaining,
next165, fixed CROSSREF8 NOT_RUN, Native011 unapproved/unexecuted, P09/A12/A13 OPEN, P10 not started
and the full P09–P20 goal ACTIVE remain unchanged.
