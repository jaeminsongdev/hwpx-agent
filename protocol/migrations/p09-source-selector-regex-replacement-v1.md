# Review selector regex replacement source profile

`hwpx-agent.source-selector-regex-replacement-candidate/v1` compiles actual regex captures and a dollar
template into distinct original Text atom edits. Four original selector scopes and explicit hidden/MEMO
body policies use the existing protected writer. This source candidate does not grant current stored
access, a product JSON route, revision commit, Native behavior or the complete SEARCH-007 contract.
Its current storage/strict request connection is qualified separately in
[the regex product profile](p09-regex-replacement-product-request-v1.md).

## One capture pass and strict template grammar

lower_review_selector_regex_candidate requires Regex mode and an operation-local whole Form proof.
Original fields, review bodies and source index are built once. The existing selector windows/policy
are resolved before matching. One regex is compiled with the original pattern/DFA/query limits; each
eligible window is scanned once with captures_iter. The optional sink records expansions alongside the
original match/provenance, not by searching each match again. Without a sink the original find_iter path
allocates no capture set and retains its result/hash/limit semantics.

Templates accept $0 and numeric groups, $name, ${name} or ${number}, and $$ for a literal dollar.
Unbraced references consume ASCII letters/digits/underscore greedily; braces delimit an exact name.
Group names and indices are resolved against that one compiled regex before scanning, even with no hits.
Unknown/out-of-range groups, overflowed indices, bare dollars or malformed braces return Template.
An existing optional group that did not participate expands to empty text. Backslashes are ordinary
replacement text, not a second escape language. Original text policy rejects control characters.

Capture values are the NFC index text, not guaranteed original spelling or source byte slices. Pattern
syntax itself is not normalized. Case sensitivity and whole-word handling use the existing matcher;
regex anchors see the clipped selected window and never concatenate across paragraph/control barriers.

## Original compiler and preservation

The original atom compiler accepts an optional private per-occurrence expansion sequence. Fixed literal
callers still pass None. Each expansion goes to the first original run contributing to its full match;
all original runs/styles remain and remaining contributing scalar ranges are deleted. The original
contiguous-origin, overlap, protection, field-cache/ancestor-field, source limits, writer integrity,
whole output reconstruction and exact outside-selected-slot byte checks remain unchanged.

Only the exact owning MEMO payload is carved out of its own field interval when policy permits it;
other/enclosing fields and cached results remain blocked. Controls are preserved, not flattened into
editable text. No matches and unchanged values return their original errors rather than fake candidates.
The inner output profile is source-regex-text-atom-output/v1; its replacement hash/bytes describe the
ordered expansion sequence. The outer receipt separately binds template SHA/size, source/index/scope,
query/policy/review regions, work counters, original and output review receipts and output integrity.
No template, query, capture values, author metadata or raw XML appears in the receipt/Debug output.

Zero-width insertion is not qualified by v1: a batch containing an actual zero-width match fails before the
writer. It is not silently skipped. The original engine suppresses empty matches immediately adjacent
to nonempty matches; that suppression is retained and independently checked against plain search.
Whole control/field/newline writes, style filters, effective visibility and complete protection remain open.
The separate [v2 insertion source profile](p09-source-selector-regex-insertion-v2.md) qualifies explicit
inverse-NFC text insertions without widening this v1 API or its product request.

## Expansion resource bounds

Each expanded value obeys the original1 MiB value limit; aggregate expanded UTF-8 bytes obey configured
result_bytes. A separate work counter includes one unit per template token resolved and per token
expanded at each accepted occurrence. Its ceiling is configured decomposed_scalars, normally1,000,000.
The counter is independent of source decomposition and output bytes: empty optional captures still cost
work. A limit failure returns no partial candidate. The exact512-unit boundary passes and the next match
fails in a17th dedicated resource case. No allocation or regex budget is silently raised.

## Verification and preserved failures

Components112 records86 passes and two failed new tests among88 cases. One styled-run fixture used a
stub header without its style definitions; the corrected positive uses the existing typed-header fixture
and preserves rejection of the original stub. The other expected a terminal empty match after a nonempty
match, contrary to the original regex adjacency rule. Its correction proves the suppressed case and then
uses a nonmatching gap, proves an actual empty match through original search and verifies batch rejection.

Recovery113 adds the work ceiling and attempts the16 affected regex cases plus the new boundary case.
It reaches the300-second compile deadline with test execution unconfirmed and confirmed owned cleanup.
The failed result is preserved. A bounded live PC observation then showed logical CPU0 at100% and a
separate maple-re process fixed to mask1 consuming CPU time. That process was not changed or terminated.

Focused114 includes the exact same17 test bodies in a new small target without compiled copies of the72
retained tests. Only the newly launched verifier selects logical CPU2/mask4 before the original Windows
limiter. The limiter already supports the lowest allowed single bit, so common guard/launcher code and
other process settings are unchanged. Actual Job readback proves mask4, one CPU, BelowNormal, CPU hard
cap6.25%, private cap8%/stop7%, RAM/commit95%, command300s, guard600s and no breakaway/kill-on-close.

All17 focused cases pass with582 fresh/final582 inputs, no diagnostics and terminal/empty/closed cleanup.
Original72 pass results and unchanged input/whole-common-code inverse checks establish89 distinct cases,
not a new89-case run or official queue acceptance. The original112 failure,113 deadline and two historical
bundle fixture warnings remain. Previous46 products and the249 queue are not replayed.

Coverage includes numbered/named/optional/whole-match/dollar expansion, distinct adjacent values/deletion,
all selectors/policies/caps, cross-run style and Hangul NFC, entities/noops, NFC ambiguity, controls, MEMO
payload/cache/enclosing fields, table protection, malformed templates/patterns, input/proof/writer limits,
zero-width rejection, many matches sharing one protection map and independent empty-capture work bounds.

Focused runtime is100.703 seconds overall,25.516 seconds for the command and1.44 seconds in libtest.
Owned Job CPU23.875 seconds, peak private1639.30 MiB or5.1452% of RAM, maximum sampled system CPU29.49%
and minimum available RAM36.2434%. Core choice and target were changed together, so this is not a controlled
benchmark or proof of the full PC-freeze cause. Evidence is implementation/p09/evidence/
p09-361-regex-replacement-components112.v1.json, p09-361-regex-replacement-recovery113.v1.json and
p09-361-regex-replacement-focused114.v1.json.

## Next product boundary

Current stored-service binding and strict product JSON are qualified in
[the regex product profile](p09-regex-replacement-product-request-v1.md). Existing literal schemas still reject
Regex mode; they are not silently expanded by this core. V2 source insertion and its current stored/
strict product binding have separate qualification in [the v2 insertion product profile](p09-regex-insertion-product-request-v2.md).
Remaining search scope/
visibility/style/filter/protection, target match_set/semantic_diff/reopen, transaction/dispatcher/DB/CAS/
execution/publication and Native/Gate qualification remain open.

Source API v12 stays incomplete with four unresolved stages, a null report and CLI exit3. Official
acceptance remains158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is
unapproved/unexecuted. P09/A12/A13 stay OPEN, P10 is unstarted and the full P09 through P20 goal stays ACTIVE.
