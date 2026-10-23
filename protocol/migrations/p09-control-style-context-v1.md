# Control style context in source formatting resolution

The resolved direct-formatting core and v9 product must not silently ignore a charStyleIDRef on an
enclosing paragraph-namespace ctrl. The selected character axis remains unresolved until its actual
semantics are qualified. This correction does not infer a Native inheritance rule or support styled
MEMO wrappers that the original source reader rejects.

## Official storage and application boundaries

The pinned official
[control model](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/ctrl.cpp)
and [text model](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/t.cpp)
both store charStyleIDRef. The reviewed local ctrl model retains its exact checksum from inspection048.
Storage declarations alone do not establish a target domain or precedence rule.

The [Hancom 2020 character-style help](https://help.hancom.com/hoffice110/ko-KR/Hwp/format/style/style(font).htm)
describes applying/removing character styles and their relationship to paragraph styles. The official
[hidden-explanation help](https://help.hancom.com/hoffice/multi/ko_kr/hwp/insert/annotations/comments.htm)
describes hidden explanations outside ordinary body display/printing. Neither UI description is a
captured source mapping or target-build proof for this implementation.

## One structural context map

Selected source segments are grouped by borrowed part path and exact element index. Each selected
part computes one parent-state map in source order. A sorted selection cursor joins text segments
without per-match XML parsing, ancestor walks or repeated linear part searches. Empty selections do
not build a context map. Existing finite source/index limits still bound the work.

Only an unqualified charStyleIDRef attribute on a ctrl in the exact paragraph namespace marks a
structurally enclosed segment uncertain. Aliased prefixes resolve by namespace, while a foreign
attribute is not interpreted as Native style metadata. No value0, matching descendant reference or
direct run is assumed to override that unknown context. t plus ctrl uncertainty counts a segment
once, using the existing coverage shape. Unrequested character predicates, sibling text, outside
scope and policy-excluded bodies retain their existing behavior.

The original filter, direct definition predicates, coverage JSON shape, v7 explicit-axis meanings,
stored source/authorization/result/final-head boundaries and all source readers remain unchanged.

## Existing source observations

Observation152 stopped before package observations because it tried to find the ctrl-model pin in
the later product scope, where that model was not declared. The KeyError failure and cleanup record
are preserved. Observation153 binds the exact reviewed model pins from inspection048 instead.

The readonly sample has10 existing paths:3 prepared fixtures and7 historical saved/reopened paths.
It observes20 XML parts,35 paragraphs,59 runs and52 text elements. Text/control-style references and
hidden explanations are all0; named CHAR definitions total10 and missing direct run/paragraph refs
are0. This sample cannot qualify the absent style/hidden conditions. Historical path labels are not
new Native attestations. Observation153 records89 fresh/final89 inputs,13.000 seconds and cleanup.
No source bytes or raw text/author/font values are emitted; no Hangul/COM/access dialog is started.

## Regressions and original admission

Components154 runs26 source cases and records24 passes/two failures; product cases do not run.
The failures used a styled MEMO wrapper and expected the new resolution stage, but the unchanged
Form reader returns Body first. That is this reader's unsupported representation boundary, not a
claim that the HWPX is universally invalid.

Recovery155 leaves all production unchanged after154. Two failed source expectations now require
the exact original FormImportError::Body and source-byte preservation, then separately check admitted
hidden-context paragraph predicates and exclusion for explicit IDs0/1. One unexecuted product oracle
similarly requires exact Import/Body for MEMO versus Resolution/Unresolved for hidden context. The
original reader rejection is neither relaxed nor relabelled as a new resolved result.

Recovery155 runs only2 repaired source cases and26 product cases, all28 pass with645 fresh/final645
inputs and no diagnostics/warnings. The24 original passes are retained with unchanged production
and inverse-verified test bodies, not rerun. There are52 distinct cases:8 new source,6 new product,
18 affected source and20 affected product. This is not one current52-case run. Other104 products,
unrelated suites and the official249 queue are not replayed;154 remains failed.

Coverage includes admitted hidden contexts/absent queries, exact original MEMO admission rejection,
unrequested character axis with paragraph predicates, policy exclusion, exact sibling/empty windows,
t/control deduplication, namespace aliases/foreign attributes,128 descendant runs, stored error
propagation, current result/next checks and preserved legacy v7 semantics. The affected original
18/20 cases preserve their own assertions, including access, quarantine/AEAD, four final-head races,
strict schemas/cursors/limits/NFC and source/privacy preservation.

Recovery155 takes127.250 seconds overall. Source command2.984 seconds/libtest0.29 seconds and product
command41.266 seconds/libtest7.64 seconds use separate serial owned Jobs. Their Job CPU is1.750 and
39.578 seconds; peak private memory1694.93 MiB or5.3198% of physical RAM. Maximum sampled system
CPU44.85%, minimum available RAM24.3244%. Logical CPU2/mask4, BelowNormal, CPU cap6.25%, private8%/
stop7%, RAM/commit95%, command300s/guard600s remain, with both Jobs active0/empty/handle closed.
These are observations, not a benchmark, process attribution or proof of a PC-freeze fix. Other
processes, OS and Defender settings are unchanged.

Evidence under implementation/p09/evidence:

- p09-361-historical-style-observation152.v1.json
- p09-361-historical-style-observation153.v1.json
- p09-361-control-style-context-components154.v1.json
- p09-361-control-style-context-recovery155.v1.json

## Remaining work

Native text/control style targets/precedence, missing-axis behavior, visibility and styled-MEMO source
admission remain unresolved pending representative originals and target qualification. The next
permission-free implementation is SEARCH-022 actual source Unicode normalization, distinct from
search-index NFC. Complete cascade/scope/filter/protection, match_set/semantic_diff/reopen,
dispatcher/storage/CAS/idempotent execution/publication and required Native evidence remain open.
Source API v12 stays incomplete/four unresolved stages/null report/CLI exit3. Acceptance stays158/249
with91 pending, next case165; fixed CROSSREF8 NOT_RUN and Native011 unapproved/unexecuted.
P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal remains ACTIVE.
