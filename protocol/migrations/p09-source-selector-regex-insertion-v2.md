# Review selector regex insertion source profile

`hwpx-agent.source-selector-regex-replacement-candidate/v2` adds exact source text insertion for
zero-width regex matches. It uses the existing capture compiler, four source selectors, explicit
hidden/MEMO policy and protected preserving writer. The original v1 API and v1 product JSON still
reject zero-width matches. Current v2 storage and strict JSON binding are qualified separately in
[the v2 insertion product profile](p09-regex-insertion-product-request-v2.md).

## Explicit insertion policy

`lower_review_selector_regex_insertion_candidate` requires
`SourceRegexInsertionPolicy::RightOriginalPointElseLeftFirstEmptyText` in addition to the existing
query, selector, body policy, replacement template, nonempty-match run policy and resource limits.
Its whole Form reconstruction proof is bound to the exact original. No caller captures, raw XML,
byte offsets, graph, default style or trusted flags are accepted.

| Source cut | Insertion owner |
|---|---|
| An original contribution exists to the right | Before that original scalar in its original text/run |
| No contribution exists to the right | After the final original scalar in its original text/run |
| The chosen original point is a tab or line break | At its outer boundary, never inside the control |
| The indexed paragraph is empty | The first admitted original hp:t; no new run or text element is invented |

The rule applies to the full original block even when a selection clips matching to a smaller window.
Consequently a cut between styled runs uses the right original run, while a cut at block end uses
the left run. All existing runs and style references remain. Empty paired hp:t and self-closing hp:t
are supported. Expanding a self-closing element changes only its original `/>` shell, with the original
qualified name, attributes and whitespace retained and the exact closing name checked independently.
An empty paragraph without an admitted original text owner is rejected rather than assigned an
implicit style or guessed position. Opaque text is not converted into an editable owner.

## Exact inverse NFC cuts

The source index retains the original scalar contributions for every NFC unit. One suffix minimum
and prefix maximum map is built per matched block, not per occurrence. Both sides of a cut must have
disjoint, correctly ordered contiguous original contributions. A cut that splits the normalized
contributions of one original scalar or crosses reordered contributions rejects the entire candidate.
It is not rounded to a nearby source position. Complete cross-run Hangul clusters retain their
original decomposed spelling when insertion does not replace them.

These are source Unicode scalar coordinates, not UTF-8 bytes, UTF-16 indices or Native caret positions.
The regex engine's suppression of an empty match immediately after a nonempty match is unchanged.
An empty query remains invalid; `(?:)` is a valid nonempty pattern that matches empty boundaries.

## One protected output transaction

Original field/review import, selector resolution and capture expansion are shared with v1. Matches
and expansions come from one original capture pass. Nonempty matches retain the existing contiguous
origin and first-original-run policy. Zero-width coordinates use the private inverse-cut plan; both
forms feed one original preserving transaction and whole output reconstruction.

Field caches, enclosing fields and observed table/cell/ancestor protection still reject edits before
writing. Only the existing exact owning MEMO payload exemption applies when its policy permits it.
Original controls remain byte-exact. Text may be inserted before/between/after controls, but matching
and replacing a control, generating new controls or inserting tab/newline text remains unqualified.
No matches and a wholly unchanged request retain NoMatches and NoChange rather than fake success.

The patch primitive `TextAtomRangeReplacement::at_control_boundary` validates the original reader,
control adjacency, ordinal, ordering, overlap and shared count/escaped-byte budgets. It addresses
only a control's outside boundary. One direct-child edge inventory serves the whole target. The
source compiler retains the field/protection checks that a low-level patch receipt cannot authorize.

Output materialization merges sorted insertion boundaries with original atoms in one pass. It does
not repeatedly insert into the middle of an atom Vec. Adjacent text tokens are merged exactly as the
original reader does; controls are not flattened. NFC projection, control-edge indexing and atom
materialization are linear in their respective source/inserted inventories, not source size times
match count. Existing regex, scalar, match, per-value, aggregate output, expansion-work, patch and
writer ceilings remain. Limit failures return no partial candidate.

## Receipts and authority

The v2 wrapper binds the insertion policy, zero-width match count, ordered insertion-coordinate digest,
exact-cut verification and text-only control-boundary/empty-text support. Each digest includes original
index identity, match ordinal, block/cut, text anchor and original atom/scalar/side. The nested regex
receipt retains template and expansion identities, selector/policy, original/output review imports,
work counters and output integrity. Its inner atom profile is source-regex-text-atom-output/v2.

The zero-width count includes selected zero-width occurrences whose expansion is empty, not only
changed ranges. The old combined zero-width/control/cache flag stays false: the v2 text-only receipt
does not grant control/cache editing. Receipts and Debug expose no private source, replacement or
capture values. Writer integrity is not current stored access, revision commit, Native attestation
or execution/publication authority.

## Component verification

Components118 records78 passes and8 failed new cases. The failed cases used an empty query, which
the original matcher rejects before regex execution. Production code and those78 passes were
preserved. Recovery119 changes only11 such inputs across the8 failed cases to `(?:)` and adds one
independent empty-query rejection test. Exact inverse hashing restores the whole prior test file.
The8 corrected cases plus1 new test pass, followed by29 affected original v1 regex/selector products.
Recovery119 checks591 fresh/final591 inputs, has no diagnostics and confirms owned cleanup.

This establishes19 new source cases plus68 affected original core/patch and29 affected original
products:116 distinct cases, not a single current-generation116-case run. Linear120 then changes
only v2 atom materialization. Whole-file inverse checks preserve the protected compiler outside
that branch and the complete prior NFC projection. Only the19 affected v2 cases are rerun and pass;
the original97 results are retained. All592 fresh/final592 inputs match, with no diagnostics and
confirmed cleanup. The original118 failure remains intact.

Coverage includes all selectors and review policies, clipped empty selections, styled run boundaries,
cross-run Hangul NFC, reordering/decomposition ambiguity, original entities and Unicode scalar edges,
leading/adjacent/trailing/1000 controls, empty paired/self-closing text, absent/opaque owners, mixed
empty/nonempty expansions, noops, field caches, table/ancestor protection, proof, privacy and limits.
Direct patch negatives cover noncontrol/out-of-range/duplicate/unsorted edges and shared budgets.

Linear120 takes102.328 seconds overall,26.500 seconds for the command and1.77 seconds in libtest.
Owned Job CPU is24.891 seconds and peak private memory1647.82 MiB or5.1719% of physical RAM.
Maximum sampled system CPU is29.31%; minimum available RAM is35.9864%. The Job uses one logical
CPU2/mask4, BelowNormal, hard CPU cap6.25%, private cap8%/stop7%, RAM/commit95%, command300s and
guard600s. It ends active0/empty/handle closed. No common guard, other process settings, OS or
Defender configuration changed. These observations are not a controlled benchmark or a PC-freeze fix.

Evidence under implementation/p09/evidence:

- p09-361-regex-insertion-components118.v1.json
- p09-361-regex-insertion-recovery119.v1.json
- p09-361-regex-insertion-linear120.v1.json

## Next product boundary

The explicit v2 policy and private candidate are connected to current stored access and a strict
product request in [the v2 product profile](p09-regex-insertion-product-request-v2.md), without widening
the existing [v1 regex product](p09-regex-replacement-product-request-v1.md). SEARCH-008 source style
selection/replacement/preservation is next.
Full search scope/effective style/visibility, control/cache/newline edits, complete protection,
target match_set/semantic_diff/reopen, dispatcher/storage/CAS/idempotent execution/publication and
required Native evidence remain outside this source profile.

Reference source API v12 stays incomplete with four unresolved stages, null report and CLI exit3.
Official acceptance remains158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN;
Native011 is unapproved/unexecuted. P09/A12/A13 remain OPEN, P10 is unstarted and the full
P09 through P20 goal remains ACTIVE.
