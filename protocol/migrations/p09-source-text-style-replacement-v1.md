# Text style reference replacement source profile

`hwpx-agent.source-selector-text-style-replacement/v1` changes the explicit charStyleIDRef of original
Text scalar contributions selected by the existing style matcher. It keeps original run and paragraph
shells, splitting only text elements where required. It is the source stage of this SEARCH-008 axis;
effective formatting and a full style transaction remain open. Its current stored/product boundary is
qualified separately by the [text-style product request](p09-text-style-product-request-v1.md).

## Source selection and reference domain

lower_review_selector_text_style_candidate requires the exact original whole Form proof, query,
one of four selectors, explicit hidden/MEMO policy, declared/definition filter and target u32 ID.
One original field/review/index and matcher pass resolves the target from the same typed catalog.
This uses the existing typed character reader's explicit text-style reference domain, not guessed
named-style inheritance or a new Native semantic interpretation. Target/source/declaration/selector/
query/filter/policy bind the receipt and operation digest; caller XML/coordinates/approval flags are absent.

Every original contribution must be nonempty, exact and contiguous. Cross-run NFC selects original
jamo rather than regenerating text; ambiguous reordering/partial decomposition rejects rather than
widening. Missing text references remain missing on unselected scalars. Controls are retained under
their original text style, not treated as editable text contributions.

## Text element rendering and independent readback

One edge scan per requested Text atom uses the original qualified TextSpan/token scanner. The renderer
copies original entity spelling and body/control bytes, splits at required boundaries and preserves
original run boundaries and all run references. Copied text shells retain QName/allowed attributes and
exact in-scope namespaces for standalone fragment validation. Unsupported text attributes and tracked
runs fail closed; no identity-bearing attribute is silently duplicated.

Field cache/enclosing field, observed table/cell/ancestor protection and the exact admitted MEMO-body
exception use the original protection context. Protection is checked before no-op elimination.
One protection map per changed part and cumulative fragment/compiled-byte limits avoid per-match
whole scans or unbounded output retention. NoMatches/NoChange and all input/output/writer limits reject
the whole request without truncating a successful candidate.

One preserving transaction and writer create output. One whole output Form/field/review import checks
the already parsed review receipt and exact compiled edits plus original gaps/tails. The original
scalar reader checks every decoded scalar/control value, every unchanged run reference and every
selected/unselected text reference. Indexed block text must remain identical.

## Explicit ID profile

The existing shape/v6 profile rejects charStyleIDRef as unknown. The additive
`hwpml-2011-text-style-static/v9` inherits only shape/v6 and adds the exact spine-document paragraph
namespace t element's unnamespaced charStyleIDRef -> Contents/header.xml CharacterProperties reference.
It does not admit charts, caption-owner extensions, arbitrary ID-like attributes, wrong sites or
namespaced attributes. Dangling/malformed references, duplicate declarations and unknown IDs still fail.
Whole-file inverse verification restores the original v1 through v8 engine and rules.

The pinned Hancom model1453388472c703a4b299a0834f425cdac16644b9 CT implementation in
fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Para/t.cpp
reads/writes this unsigned attribute. [Hancom's schema explanation](https://tech.hancom.com/python-hwpx-parsing-2/)
also places it on mixed-content t. These establish attribute vocabulary, not target behavior or
visible formatting. The domain follows the existing typed reader; actual Native semantics remain unqualified.

## Qualification and preserved failures

Components131 fails compilation because the independent test helper used a crate-private attribute
method; no tests ran. Recovery132 changes only that helper to use public raw attribute spans and XML
unescaping:5 pass and11 fail in output patching. Diagnostics133/134 repeat one failed case only and
capture the closed Patch variant; their constrained code filters return no specific code. They do not
prove a particular issue code or accept a product/component result.

ID recovery135 selects the explicit v9 output pipeline, identical to the old preserving pipeline except
its profile. It passes11 failed cases,1 writer-limit recheck and5 new ID tests:17 current cases with
616 fresh/final616 inputs, no diagnostics/warnings and confirmed cleanup. Four unchanged negative cases
that finish before output are retained from132, for21 distinct cases, not a single current21-case run.
The writer assertion is strengthened from any error to the exact Writer rejection. Prior successful
source59, products47+18, unrelated suites and the official249 queue are not replayed.

Coverage includes entities/partial text/cross-run Hangul, controls, declared/definition filters,
regex/case/word/four selectors, nested review policies/exclusion before caps, cache/enclosing field/
table/tracked protection, ambiguous NFC, missing references, alias namespaces/IDs, stale source/proof/
scope, noops/limits/privacy,128 matches and independently checked target declaration identity.
New ID cases prove old profiles still reject this attribute, v9 resolves the exact domain, invalid/
dangling/duplicate IDs reject, wrong sites/attribute namespaces reject and foreign elements stay opaque.

Overall108.485 seconds, command28.797 seconds, libtest4.79 seconds and owned Job CPU27.219 seconds.
Peak private memory1662.26 MiB or5.2172%; maximum sampled system CPU29.44%, minimum available RAM29.5011%.
Logical CPU2/mask4, BelowNormal, CPU cap6.25%, private8%/stop7%, RAM/commit95%, command300s/guard600s
remain, with final active0/empty/handle closed. This is not a benchmark or a PC-freeze fix claim.
Other processes, OS and Defender settings are unchanged. Evidence under implementation/p09/evidence:

- p09-361-text-style-components131.v1.json
- p09-361-text-style-recovery132.v1.json
- p09-361-text-style-failure133.v1.json
- p09-361-text-style-patch-code134.v1.json
- p09-361-text-style-id-recovery135.v1.json

## Remaining product and phase work

The [current stored and strict product binding](p09-text-style-product-request-v1.md) passes18 new
product cases with619 fresh/final619 inputs and confirmed cleanup. Source21 and previous products65
were not replayed or promoted to that new product graph. Next is paragraph/named
replacement, effective cascade/visibility, full selector/filter/protection, target match_set/semantic_diff/
reopen and dispatcher/storage/CAS/idempotent execution/publication plus required Native evidence remain.
Reference source API v12 stays incomplete/four unresolved stages/null report/CLI exit3. Acceptance
remains158/249 with91 pending, next case165; fixed CROSSREF8 NOT_RUN and Native011 unapproved/unexecuted.
P09/A12/A13 stay OPEN, P10 is unstarted and the full P09 through P20 goal remains ACTIVE.
