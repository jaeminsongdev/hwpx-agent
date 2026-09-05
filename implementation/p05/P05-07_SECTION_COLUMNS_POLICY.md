# P05-07 section/column policy

- Scope: current-PC licensed Hangul 2020 `11.0.0.9136` x86, direct HWPX section/column semantics
- Contract: `hwpx-agent.section-columns/1`
- Source lock: `source-lock-P00-20260901-v9-final-current-scope`
- Locked source SHA-256: `c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`
- Reasoning/review mode: `max`

## Source and target profile

The machine-readable KS X 6101 reform-03 records identify Appendix E `secPr`, `colPr`, `colLine`,
`colSz`, `colCount`, `sameSz`, and `sameGap`. They state that `colSz` carries each column width and
inter-column gap when widths differ, while `sameGap` applies only when widths are equal. The pinned
Hancom OWPML model at commit `1453388472c703a4b299a0834f425cdac16644b9` additionally locks the
column types `NEWSPAPER|BALANCED_NEWSPAPER|PARALLEL`, layouts `LEFT|RIGHT|MIRROR`, separator line
tokens, and line-width tokens.

The exact current-2020 synthetic section has one `secPr` and one `ctrl/colPr`: empty ID,
`NEWSPAPER`, `LEFT`, one equal-width column, and zero gap. This is the exact installed-target
baseline. Official 2024 source defines the structural vocabulary but is not runtime compatibility
evidence for this PC.

## Public model and section boundaries

- One ordered HWPX spine section part is one typed `SectionColumns` value.
- Every boundary between adjacent ordered section parts is an explicit `SectionBoundary`; the
  implementation never invents a page-side or continuous-break policy from that boundary.
- A section contains one required `secPr` in a top-level body paragraph and one or more ordered
  `ctrl/colPr` spans. Multiple spans model a column-layout change within the same section.
- `NEWSPAPER`, `BALANCED_NEWSPAPER`, and `PARALLEL` remain distinct. Balance is not inferred from
  rendered height or rewritten as ordinary newspaper flow.
- `LEFT`, `RIGHT`, and `MIRROR` remain distinct flow layouts.
- Control IDs are bounded ASCII identifiers. Empty IDs are retained because the current target
  emits them; arbitrary XML and unrestricted identifier text are not public inputs.

Page-side start/restart belongs to P05-08. Package manifest/spine publication and end-to-end
creation are exercised by the P05-07 target fixture rather than being hidden inside the XML value
model.

## Header and section-sequence consistency

Attempt 17 exposed a fixture-publication defect: the package contained two section parts and two
linear spine entries, while the current-profile `hh:head/@secCnt` still declared one section.
The graph and section-value checks alone did not detect the contradiction. The pinned Appendix C
source declares `secCnt` as a required non-negative integer; current document admission additionally
requires at least one section, consistent with the existing nonempty sequence contract.

- `read_header_section_count` reads only the namespace-qualified current-profile header root count;
  it is not a complete header/style validator. Wrong roots, missing/namespaced/duplicate count
  attributes, invalid decimal values and configured count/input/element bounds reject.
- `read_sequence_with_header` compares the declared count to the entire supplied sequence before
  lifting any section. The caller remains responsible for graph closure and the exact ordered
  spine; this API must not be advertised as independent package-closure verification.
- `replace_header_section_count` requires an explicit prior count and a bounded new count. It
  changes only the root attribute's preserving value span, retains all other header bytes and
  quote style, reparses the output, and returns source/output digests and the changed byte range.
  It never creates or removes sections itself; the caller publishes header, manifest and section
  changes atomically after complete package verification.
- The target fixture now updates one to two before publication, and its inspector uses the
  header-aware sequence admission in addition to its exact manifest/spine/part/text checks.
- The original v2 fixture and failed actual traces remain untouched. The v3 fixture differs in
  only the header count. Actual Hangul save/reopen/render acceptance remains open until rerun.

Repair evidence and remaining validation are in `P05-07_SECTION_COUNT_REPAIR.md`.

## Equal and custom column rules

The caller supplies the printable body width already validated by P05-06.

- Equal columns store count and one following-column gap. A one-column layout requires zero gap.
- Checked `gap * (count - 1)` must leave every column at least 284 HWPUNIT, the deterministic 1 mm
  compatibility floor exposed by the official model.
- The metric records total gaps, total column width, floor width, and any indivisible equal-width
  remainder without guessing which rendered column receives a device-specific remainder.
- Custom columns store one ordered `colSz` per declared column. Every width is at least 284
  HWPUNIT, each gap is bounded, the last following gap is zero, and widths plus gaps consume the
  printable body exactly. Mismatch rejects instead of stretching or clipping.
- A separator is optional and, when present, has one typed official line style, one typed official
  width, and a 24-bit RGB color.

## Preservation and failure boundary

The reader accepts a standalone namespaced `hp:colPr`, one current-profile section part, or a
bounded ordered sequence of section parts. Missing/duplicate/misplaced `secPr`, foreign namespace,
unknown attributes or children, invalid numbers/booleans/enums/colors/IDs, inconsistent counts,
impossible widths, and limit excesses fail closed.

The patch lowerer selects a `colPr` by bounded ordinal, replaces only its preserving XML outer byte
span, reparses the complete section, and proves that every unselected typed span is unchanged. The
receipt binds source/output SHA-256, selected ordinal, replaced half-open span, output size, and
checked metrics. Source bytes are never edited in place.

## Deferred evidence

Pure tests prove typed lift/lower, sequence boundaries, equal/custom arithmetic, separators,
negative cases, deterministic corpus, and surgical span preservation. They do not yet prove actual
multi-section pagination, visual balance, column separator rendering, Hancom normalization, print
output, arbitrary existing documents, or Hangul 2022/2024. Those claims stay unverified until the
disposable exact Hangul 2020 multi-section save/reopen/render target and later machine Gates pass.
