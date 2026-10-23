# P09 source definition style search v3

`hwpx-agent.product-source-search-request/v3` adds `find_definition_style` through the existing
authenticated mapped-source search adapter. It compares actual typed source definition values, not
an inferred effective formatting cascade, hidden visibility, Native layout or full SEARCH-003 support.

The optional [character and paragraph detail product extension](p09-detail-definition-product-v1.md) carries51
predicate families through the same explicit axes, v3 scopes and existing v4 definition compatibility.
Canonical expansion beyond16 KiB is now rejected before sealed-source access, without increasing either limit.

## Strict definition filter

The common source/head/key/plan/scope envelope and16 KiB bound remain. The new operation uses the
existing literal query/options plus a definition_filter object. Duplicate/unknown keys, null/array filters,
invalid enum/numeric/RGB values, empty predicates, unused axes and mixed style_filter are rejected before
source reads. V1/v2 reject the new operation and any definition_filter, including null. V3 can also use
the earlier operations, but definition_filter is admitted only for find_definition_style.

Character predicates are optional bold, italic, height_hwpunit and text_rgb (three u8 values). Any such
predicate requires character_source of run_property, text_style or named_style. Paragraph alignment
requires paragraph_source of direct_property or named_style; alignment is one of justify, left, right,
center, distribute or distribute_space. Specifying an axis without its corresponding predicate is invalid.
False is a requested Boolean value, not an absent condition.

## Original typed source binding

The existing catalog read_header delegates to the unchanged CharacterStyleCatalogReader and
ParagraphStyleCatalogReader and checks named-style relationships, dense IDs, counts and original
definition references. One crate-private bridge exposes those owned typed catalogs to the new source
query. It does not add a public caller-supplied catalog or duplicate header algorithm.

Every present paragraph/run/text reference in indexed text segments must resolve in its source domain.
Missing references stay missing and are counted; they are not zero or an implicit named-style fallback.
Text_style follows the original typed character reader's reference domain, while named_style follows
the paragraph's named style to its explicit charPr/paraPr links. nextStyle is not based-on inheritance.
Absent effect elements retain the existing typed reader's qualified value semantics; this does not invent
missing reference IDs or cross-axis precedence.

Reference links are precomputed once; all contributing original scalars of a normalized match must
satisfy the chosen definitions. Empty matches do not manufacture formatting. The existing accepted
match/point limits and whole response bound apply. Requests/results bind original source/index,
inspection and header digests, selected scope, query and definition predicate. Source/header changes
require a new result. No raw header, font names or query plaintext are included in results/Debug.

Definition results use `hwpx-agent.source-definition-style-search/v1`; stored and product preparation
receipts use v3 for this new variant. Earlier result variants retain their original stored shapes.
all_present_indexed_references_resolved=true covers only present references in this partial corpus.
Missing-axis counts and implicit_cascade_or_hidden_visibility_qualified=false must be kept with it.

The separate [selected direct-formatting resolution profile](p09-source-resolved-formatting-v1.md)
assesses required axes before query execution and rejects unresolved selected source semantics rather
than treating them as false predicates. It reuses this original typed catalog and direct predicates;
v3's explicit-axis meaning and its receipts are unchanged. Its separate
[stored/v9 product binding](p09-resolved-style-product-v9.md) qualifies20 new access/search/next cases;
Native cascade/visibility remain unqualified.

## Current access and verification

The private result enum shares the original document.write, sealed current Result, scope/head,
ACL/quarantine/AEAD, complete Form reconstruction and final consumer head checks. No unchecked
result accessor, source overwrite, ingest, revision commit, durable key claim, CAS, CLI/server dispatch,
execution or publication is added. Fresh verification rechecks service access/source, not the query.

Components051 records three passes and six failures on a new synthetic fixture's effect ordering.
Diagnostics052/053 independently identify character_style_unsupported_shape. The fixture had appended
bold then italic after higher-ranked effects. Only the fixture builder changes to insert italic then bold
before the existing effects; the original typed reader and product code stay unchanged.

Recovery054 executes nine core cases (eight affected by the fixture plus one independent original
reader/catalog diagnostic) and20 product cases (six v3 plus14 affected v1/v2). All29 pass with
449 fresh/final449, no diagnostics and terminal/empty/closed owned Jobs. The independent filter case
from051 remains unchanged and is not replayed, for30 distinct definition-path cases. The previous39
core passes are preserved by exact original-code/test-body checks, not rerun or promoted as fresh v3
execution. Earlier header-dependent negative cases are revalidated with the admissible fixture.
All original failed receipts remain failed. Unrelated286 stored cases and the official queue are not run.

Source definition matching does not qualify effective cascade/hidden visibility, complete SearchScopeSelector,
target match_set/semantic_diff/reopen, Native behavior or the P09 Gate. Queue158/249, remaining91,
next165, P09/A12/A13 OPEN, fixed CROSSREF eight NOT_RUN, Native011 unapproved/unexecuted
and P10 not started remain unchanged.

The additive [v4 file-body search](p09-source-review-text-search-v4.md) admits original hidden/MEMO
body text with explicit inclusion policy. It does not change this v3 definition filter or qualify
effective formatting, native visibility or a combined review-body/style operation.

The separate [review selector style core](p09-review-selector-style-core-v1.md) now combines explicit
definition predicates with four source windows and review policy. It shares the original all-contributor
predicate/lookup; its stored/strict JSON/cursor path is qualified in
[the v7 product profile](p09-review-selector-style-product-v7.md). This v3 request meaning is unchanged.

The [partial character-property replacement source profile](p09-source-character-style-replacement-v1.md)
shares one original typed-definition import for predicates and its exact replacement declaration anchor.
This does not widen the v3 search request or qualify paragraph/named/effective-style replacement.

The separate [text-style replacement source profile](p09-source-text-style-replacement-v1.md) reuses the
existing explicit text-style character domain and typed target anchor. It preserves run references
and keeps Native/effective-style unqualified. Its separate
[current stored/product binding](p09-text-style-product-request-v1.md) passes18 new preparation/access
cases; neither this source-search request nor that candidate preparation commits a revision or authorizes execution.

The separate [paragraph/named source profile](p09-source-paragraph-style-replacement-v1.md) moves exact
paragraph and PARA named-style declaration anchors from this same typed catalog in one pass. It does
not change existing predicates/receipts/character lookup or reinterpret nextStyle as inheritance.
Its separate [current stored/product paragraph binding](p09-paragraph-style-product-request-v1.md)
passes21 new preparation/access cases. Native/effective-style behavior and complete search execution
remain unqualified; these candidates do not commit revisions or claim durable execution authority.
