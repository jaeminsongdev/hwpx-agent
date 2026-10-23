# Paragraph style reference replacement source profile

`hwpx-agent.source-selector-paragraph-style-replacement/v1` replaces either paraPrIDRef or styleIDRef
on whole matched original paragraphs. It requires explicit WholeMatchedParagraphWithinScope extent
and rejects a clipped selector instead of widening it. This is a source reference candidate for
SEARCH-008, not effective style application, revision commit or Native qualification. Its separate
[current stored/product binding](p09-paragraph-style-product-request-v1.md) qualifies preparation and
fresh access for both axes without widening this source profile.

## Target definitions and matching

SourceParagraphStyleTarget distinguishes ParagraphProperty from ParagraphStyle. The first requires an
existing original typed paragraph property; the second requires an original named style whose type is
exactly PARA. CHAR, unknown/missing type and absent or wrong-domain targets reject. The index moves
original declaration anchors into both maps during the same owned catalog pass as the unchanged
character declaration index; it does not rescan the header for each target or match.

The new matcher reuses the original declared/definition predicates, query options and review selector
windows. It resolves scope and the typed catalog once and moves the exact window map into the compiler,
without cloning/re-resolving it. All original nonempty/exact/contiguous scalar contribution checks remain.
The request digest binds the source query, selector/policy/filter, explicit extent, typed target,
original declaration anchor and changed-paragraph set.

## Whole paragraph extent

All indexed blocks of every matched paragraph must be wholly covered by the selected windows. Document,
section and node-set scopes retain their existing source meanings; a selection must cover the paragraph's
whole indexed extent, including its separate blocks. A partial text query can choose a whole paragraph
only under the explicit extent policy; a partial selector cannot grant that extent. This is the mapped
source-index contract, not complete hidden/native-flow or arbitrary opaque-content coverage.

Repeated matches select one paragraph once. Changing one axis leaves the other paragraph reference and
every original run/text reference unchanged. Missing references are added only on the chosen paragraph
and axis; they are not assumed to be property0. styleIDRef replacement does not copy target charPr/paraPr
values into direct references or prove an effective rendered change. nextStyle is not inheritance.

## Protection and attribute edits

One original field/review context handles cache ranges and the exact owning MEMO-body exemption.
The whole paragraph span is checked against protected field intervals, even when its query does not
touch cached text. Other enclosing fields still block an admitted MEMO body. Protection precedes
no-op elimination.

Each touched part builds the original2N inherited protection map and one additional N pass for inherited
tracked flags and a protected-subtree prefix index. A paragraph therefore cannot bypass an unqueried
locked descendant, tracked ancestor, paraTcId/charTcId or observed tracked marker. Subtree checks use
prefix counts and binary search rather than a complete descendant scan per match. The receipt records3N
element visits per touched part. This is observed protection, not complete protection authority.

One deduplicated attribute intent per changed paragraph replaces the original value or inserts one
unsigned attribute. One preserving transaction uses the existing v9 ID/profile/writer pipeline; the
old pipeline changes only helper visibility. Original quote/tag/namespace/entity/control/child bytes
outside selected attribute edits remain exact. Match, intent, request/output and writer limits reject
the whole candidate; one invalid/protected paragraph prevents any output.

One output package/Form/field/review import verifies exact edits and gaps/tails, all paragraph reference
values in changed parts and byte-exact unchanged parts. The original scalar reader independently checks
all scalar/control values and run/text references; indexed block text and already parsed review receipts
must agree. No source artifact is overwritten or committed.

## Qualification and preserved failures

Components140 fails compilation before tests because Properties has no get method. Recovery141 changes
only that condition to the original iter API, preserving the exact PARA predicate. It passes37 of38
cases; the remaining atomicity fixture uses a paragraph lock attribute rejected by the original reader
as Body before the intended protection check. Production and all other test bodies remain unchanged.

Fixture recovery142 changes that one input line to a previously admitted locked-table descendant and
runs only the failed atomicity case:1 pass,628 fresh/final628 inputs and confirmed cleanup. The37 passes
remain bound to unchanged production/fixtures and inverse-verified test bodies. These are20 new paragraph
cases plus18 affected original definition/selector cases,38 distinct cases, not a single current38-case
run. The140/141 failures are preserved. The two unchanged fixture dead-code warnings are package and
with_body in review_scope_fixture.rs at lines5 and6; their source and warning records remain.

Coverage includes both axes, partial-query/whole-paragraph semantics, four selectors and clipped/multiple
block rejection, typed target anchors/PARA versus CHAR, declared/definition filters, missing axes,
entities/quotes/namespaces/cross-run Hangul/controls, nested hidden/MEMO policy, unqueried cache/locked
descendant/tracked protection including noops, stale source/proof/scope, regex/case/word, errors/limits,
128 paragraphs with one protection map,128 matches with one edit, privacy and atomic multi-paragraph failure.
Previous83 product cases, unrelated suites and the official249 queue are not replayed or promoted.

Recovery142 takes85.218 seconds overall,4.578 seconds for its command and0.12 seconds in libtest.
Owned Job CPU is2.125 seconds; peak private memory574.51 MiB or1.8032% of physical RAM. Maximum sampled
system CPU47.16%, minimum available RAM28.4418%. Logical CPU2/mask4, BelowNormal, CPU cap6.25%, private8%/
stop7%, RAM/commit95%, command300s and guard600s remain, with final active0/empty/handle closed. These are
run observations, not a benchmark or proof of a PC-freeze fix; other processes/OS/Defender are unchanged.

Evidence under implementation/p09/evidence:

- p09-361-paragraph-style-components140.v1.json
- p09-361-paragraph-style-recovery141.v1.json
- p09-361-paragraph-style-fixture-recovery142.v1.json

## Remaining product and phase work

Current stored and strict product binding for these two paragraph axes passes21 new cases with635
fresh/final635 inputs through the linked product profile. Effective cascade/
visibility, full selector/filter/protection, target match_set/semantic_diff/reopen, dispatcher/storage/
CAS/idempotent execution/publication and required Native evidence remain open. Source API v12 stays
incomplete/four unresolved stages/null report/CLI exit3. Acceptance stays158/249 with91 pending, next
case165; fixed CROSSREF8 NOT_RUN and Native011 unapproved/unexecuted. P09/A12/A13 remain OPEN, P10 is
unstarted and the full P09 through P20 goal remains ACTIVE.
