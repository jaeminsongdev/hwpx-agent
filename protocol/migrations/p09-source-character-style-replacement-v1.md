# Character property replacement source profile

`hwpx-agent.source-selector-character-style-replacement/v1` applies an existing original character
property to the exact source Text scalars selected by a style-aware search. It handles partial runs,
cross-run NFC contributions and nested review bodies in one preserving transaction. This is the
character-property source stage of SEARCH-008, not completion of its whole style/transaction contract.

## Original selection and replacement definition

lower_review_selector_style_candidate takes the original whole Form proof, source query, one of the
four selectors, explicit hidden/MEMO policy, declared/typed-definition filter and target character-property
ID. It accepts no caller XML, source byte offsets, graph, guessed defaults or trusted flags. The original
style matcher validates all contributing original scalars and excludes bodies/styles before match caps.

The target must exist in the original typed header catalog. Matching and target lookup share one
definition import. The target anchor is moved from that same typed catalog into a private index, not
reconstructed by another header scan; temporary relationship indices are dropped before ownership
transfer. The receipt binds the exact original declaration and target ID, not just a count or default.
An independent full catalog import checks the exact declaration anchor in a separate test oracle.

Each selected match needs a nonempty, exact, contiguous original contribution range. Partial NFC
decomposition and disjoint/reordered source selections are rejected, not widened. Cross-run Hangul
matches can select all their original jamo while retaining their original spelling. Missing original
run references stay missing on unselected text; they are not treated as character property0.

## Partial runs and nested edits

The compiler groups selected source atom/scalar ranges by original text and run. It uses the original
qualified TextSpan reader and XML token-boundary scanner once per requested atom. Original entity
spellings and text/control bytes are copied rather than regenerated from normalized search text.
Only required text/run boundaries are split; original runs are never merged with one another.

New run shells retain the original qualified name and allowed attributes, replacing/adding only the
explicit charPrIDRef. They carry the exact original in-scope namespaces so independently validated
fragments do not depend on guessed prefixes. Existing local declarations and text/control child bytes
are retained. Redundant namespace declarations and the new run/text shells mean this profile promises
outside-original-run byte preservation and per-scalar style preservation, not unchanged run count or
byte-identical shells inside an edited run.

Opaque/control items remain once and under their original run property. Tabs/line breaks keep their
original values and bytes. A match that includes an editable control scalar is rejected. Runs with
charTcId and unsupported run attributes are not duplicated or restyled as ordinary text. Field caches,
enclosing fields and observed table/cell/ancestor protection reject requests, including noops, before
writing. Only the existing exact owning MEMO body exemption applies when its policy permits it.

Nested selected hidden/MEMO/table/note runs are rendered before their enclosing selected run. Child
edits are consumed into the enclosing edit so the original patch receives no overlapping byte edits.
One original SpliceElements transaction, existing ID/preservation rules and writer build one output;
there is no intermediate package or per-match source reconstruction.

## Output readback and resource limits

One whole output import rebuilds Forms, fields and review bodies. The original review receipt checks
reuse that parsed review import rather than importing it again. Changed parts are compared against
compiled replacement bytes and exact original gaps/tails. All original decoded scalars and supported
control values are read again; every original point must retain its original run/text reference unless
that point was selected for the explicit replacement property. Indexed block text is also compared.

Input matching, provenance, patch intent/fragment, writer and output limits remain. Namespace/run/text
shell growth and nested intermediate fragments count toward cumulative compiled-byte limits. Piece
accumulation is checked before retention, not only after building a potentially large output. Grouping
and source-edge planning avoid per-match whole scans and repeated middle insertion into arrays.
Limits reject the whole request; no truncated successful candidate is returned.

NoMatches and NoChange remain errors. Style predicates have no original contributors for zero-width
matches, so those are not editable style matches. Literal/regex, case/whole-word, four selectors and
review-body policy retain the original matcher meanings. This profile does not replace source text.

## Qualification evidence

Components126 passes18 new style cases plus40 unchanged affected definition/selector/review/atom-range
cases:58 total,603 fresh/final603 inputs and confirmed cleanup. Exact inverse checks restore the original
literal/regex compiler, patch API/transaction, atom writer, typed-definition matcher, review validation
and no-target style search outside the declared additions. Current product/unrelated suites and the
official249-case queue are not replayed or promoted to style-mutation product support.

Target127 replaces the extra target header scan with the original typed declaration index and adds one
independent declaration oracle. It reruns only19 affected style cases; the40 original passes are retained.
All604 fresh/final604 inputs match and cleanup is confirmed. These are59 distinct component cases,
not a single current-generation59-case run. The two compiler warnings are dead-code helpers package and
with_body in the unchanged tests/support/review_scope_fixture.rs at lines5 and6; they remain recorded.

Coverage includes partial/adjacent/many matches, entity spelling, cross-run Hangul NFC, original run
boundaries, controls, both filter families, all selectors and clipped regex windows, composed nested
hidden/MEMO edits, exclusion before caps, caches/enclosing fields, table locks, ambiguous NFC, missing
references, namespace aliases, foreign/stale proof/scope, noops, invalid target/filter, tracked changes,
output/writer/match limits, privacy, immutable inputs and exact typed declaration identity.

Target127 takes107.500 seconds overall,30.359 seconds for the command and5.42 seconds in libtest.
Owned Job CPU is28.844 seconds; peak private memory1659.40 MiB or5.2083% of physical RAM. Maximum
sampled system CPU is54.53%; minimum available RAM35.5320%. The owned Job retains logical CPU2/mask4,
one bit, BelowNormal, hard CPU cap6.25%, private cap8%/stop7%, RAM/commit95%, command300s and guard600s.
It ends active0/empty/handle closed. Common guards, other processes, OS and Defender settings are
unchanged. These observations are not a controlled benchmark or proof of a PC-freeze fix.

Evidence under implementation/p09/evidence:

- p09-361-style-replacement-components126.v1.json
- p09-361-style-replacement-target127.v1.json

## Remaining SEARCH-008 contract

The [current stored-service and strict product-request binding](p09-character-style-product-request-v1.md)
now qualifies these private character-property candidates with18 new product tests,608 fresh/final608
inputs and confirmed cleanup. Source core59 and original products47 were not replayed or promoted to
the new product test graph. Paragraph/named/text-style replacement, effective formatting/cascade/visibility, the complete
SearchScopeSelector/filter contract, complete protection, target match_set/semantic_diff/reopen and
dispatcher/storage/CAS/idempotent execution/publication plus required Native evidence remain P09 work.
Changing a declared run reference is not proof of a visible formatting change when other axes apply.

The source API v12 remains incomplete with four unresolved stages, null report and CLI exit3. Official
acceptance remains158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is
unapproved/unexecuted. P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal is ACTIVE.
