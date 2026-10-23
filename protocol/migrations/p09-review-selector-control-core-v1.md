# Review selector control source profile

`hwpx-agent.source-review-selector-control-search/v1` finds observed structural controls in the four
original selector scopes and explicitly admitted review bodies. This is the pure source core profile;
its current storage/strict JSON/next connection is qualified in [the v8 product profile](p09-review-selector-control-product-v8.md).

The separate [text-control replacement source profile](p09-source-text-control-replacement-v1.md)
now checks complete original atomic Tab/LineBreak coverage and observed protections. The original
search body is mechanically forwarded with its existing windows; the discovery contract below and
other control kinds do not gain replacement or execution authority.

## Actual control membership

SourceReviewScopeIndex.find_control takes Document, Section, NodeSet or an index-bound NFC Selection,
the two explicit SourceReviewTextPolicy Booleans, a closed SourceControlKind and a finite result cap.
The original selector resolver optionally captures its existing original part/node intervals alongside
the unchanged text windows. It does not rebuild the node catalog per control.

A control is included when its actual control_anchor START is inside the half-open source range.
An object node can therefore include its own control even when its enclosing paragraph begins outside
that node. Selecting a descendant paragraph does not select an ancestor control whose start lies outside.
The text scope receipt and its selected_paragraphs/blocks/scalars remain text coverage, not a substitute
for control membership. An anchor-start match does not mean that the whole control subtree is selected
or writable. Section scopes use original section identities and parts, not repeated local XML IDs.

## NFC selection projection

Both original selector endpoints and the index fingerprint are validated first. An endpoint must also
separate an original prefix from its suffix. NFC reordering can yield a legal text-only selection whose
original contributions are not a contiguous prefix; such a control endpoint returns Scope rather than
guessing or widening the range.

The two endpoint text elements are read with the original TextSpan reader, at most once each. A lexical
atom start plus decoded-scalar edge orders a control start relative to a text atom or a tab/lineBreak.
No element occurs inside a text atom, so no new XML character decoder or scalar-to-byte editor is needed.
These positions are not advertised as XML byte edit ranges or live Native coordinates.

A noninitial boundary is just after the last original prefix scalar; an initial boundary is before the
first original scalar. An empty block uses its paragraph start-tag end. Equal endpoints select no controls.
Different blocks can delimit a nonempty source gap despite selecting zero text scalars. Leading/trailing
controls are not inferred from a selected paragraph; Document, Section and actual NodeSet can select them.
Original text policy still rejects raw CR/LF and control-character references such as &#13; as text:
an explicit supported hp:lineBreak is a distinct admitted atom.

## Policy ordering navigation and bounds

Only the original inspection's known kind and parent-site inventory is searched; unknown/foreign wrappers
are not traversed. Hidden explanation and MEMO body exclusion happens before match caps. Exclusion counts
are controls of the requested kind inside the selected range, not application visibility. A wrapper itself
belongs to its original containing paragraph; excluding a body does not relabel its wrapper as hidden.

Accepted matches are sorted once by spine and actual control start. This corrects the original inspection
visit order, where an enclosing paragraph can be visited before its nested body. Parallel region labels
remain attached in the retained result. The additive ControlRegions navigation branch binds the entire
result and context plus the control occurrence and region. Forward/backward, explicit wrap, exhaustion
and cursor validation reuse the original engine without rerunning the query or importing XML.

Kind, cap, source/index/inspection/scope, both policy Booleans and the profile bind the request receipt.
The whole result is independently bounded and an overflow is an error, not truncated success. No text,
author metadata, raw XML, action route, source write, CAS or durable access permission is added. Control
parameter semantics, effective visibility/style, Native flow and execution authority remain false.

## Verification and preserved failure

Components107 records58 passes and one failed new fixture expectation across59 cases: twelve new control
cases and47 affected original selector/review/style/inspection/navigation cases. The failed fixture treated
raw CR/LF and &#13; as admitted text, but the original reader rejects them with text_flow_invalid_text.
Production and the58 passing test bodies remain unchanged. The corrected test additionally checks those
exact import errors and verifies admitted character references plus explicit tab/lineBreak projection.

Recovery108 executes only that one case and passes, retaining the58 previous passes by exact input and
whole-test-file inverse checks. It confirms566 fresh/final566 inputs and owned cleanup. This is59 distinct
component cases, not a fresh59-case rerun, official queue acceptance or current product-route support.
The original failed result and the two existing unused fixture package/with_body warnings remain.

Recovery takes74.719 seconds overall,2.016 seconds for the command and0.02 seconds in libtest. Owned Job
CPU is1.922 seconds; peak private memory is572.51 MiB,1.7969% of physical RAM. Maximum sampled system CPU
is11.64% and minimum available RAM40.4980%. The Job ends active0/empty/handle closed. One CPU affinity1,
BelowNormal, CPU cap6.25%, private cap8%/stop7%, RAM/commit95%, command300s, guard600s and before/after
input checks remain. These are run observations, not a benchmark or proof that PC freezes are resolved.
Evidence is implementation/p09/evidence/p09-361-selector-controls-components107.v1.json and
implementation/p09/evidence/p09-361-selector-controls-recovery108.v1.json.

## Remaining product and phase work

Current stored access, strict JSON and next binding are qualified separately in
[the v8 product profile](p09-review-selector-control-product-v8.md).
The existing v2 find_control keeps its original paragraph-based scope; v5/v6/v7 text/style selectors do
not silently gain the new control operation. Whole SearchScopeSelector, effective cascade/visibility,
source coverage/Native flow, replacement/conversion/protection, match_set/semantic_diff/reopen and
transaction/dispatcher/DB/CAS/execution/publication remain open.

Source API v12 is incomplete with four unresolved stages, a null report and CLI exit3. Official acceptance
remains158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is unapproved/unexecuted.
P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal stays ACTIVE.
