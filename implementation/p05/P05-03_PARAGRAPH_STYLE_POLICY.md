# P05-03 paragraph-style policy

- Contract: hwpx-agent.paragraph-style/1
- Runtime profile: licensed current-PC Hangul 2020 11.0.0.9136 x86
- Head namespace: http://www.hancom.co.kr/hwpml/2011/head
- Paragraph compatibility namespace: http://www.hancom.co.kr/hwpml/2011/paragraph
- Core namespace: http://www.hancom.co.kr/hwpml/2011/core
- Implementation: hwpx_package::paragraph_style

## Source and runtime boundary

The structural source is the locked official KS X 6101 reform-03 machine response,
ks-x-6101-machine-content-20260901, SHA-256
c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4. Appendix C defines the
header paragraph and border/fill structures; Appendix F supplies shared line types, widths, colors
and fill types. These 2024 records are a structural cross-check only and do not qualify another
Hangul release or prove that this PC's 2020 runtime implements every later schema option.

The executable profile is the exact header.xml emitted by the P04-09 VS-0 builder and already opened
by this PC's licensed Hangul 2020. It contains twenty dense paraPr IDs, three dense tabPr IDs, one
1-based numbering ID, no bullet domain and two 1-based dense borderFill IDs. The second border fill
contains the only referenced fill form: a winBrush with faceColor="none", hatchColor="#999999" and
alpha="0". That observed 2020 output is retained even though the later shared RGB XSD is narrower.
No user document, installed-style enumeration, arbitrary path, COM/HAction call or Hangul UI is an
input to P05-03.

## Typed paragraph model

ParagraphStyleCatalogReader admits a bounded full hh:head or a P05-03 hh:refList fragment through the
P03 preserving XML tree. A full header supplies external tab, numbering and bullet ID domains. A
standalone fragment requires those domains as an explicit typed argument; they are never guessed or
silently synthesized.

Each paragraph style types:

- horizontal JUSTIFY/LEFT/RIGHT/CENTER/DISTRIBUTE/DISTRIBUTE_SPACE and vertical
  BASELINE/TOP/CENTER/BOTTOM alignment;
- optional LTR/RTL text direction, condense 0 through 75, font-line-height, grid, line-number and
  checked-bullet switches;
- direct NONE/OUTLINE/NUMBER/BULLET heading or the exact 2021 metatag current/fallback switch,
  including level 0 through 9 and typed numbering/bullet closure;
- Latin KEEP_WORD/HYPHENATION/BREAK_WORD, non-Latin KEEP_WORD/BREAK_WORD, widow/orphan,
  keep-with-next, keep-lines, page-break-before and BREAK/SQUEEZE/KEEP wrapping;
- East-Asian/English and East-Asian/number automatic spacing;
- exact current and fallback margins, with the schema spelling `intent`, signed integer values and
  CHAR/HWPUNIT units;
- PERCENT/FIXED/BETWEEN_LINES/AT_LEAST line spacing, signed schema integer value and CHAR/HWPUNIT
  unit. PERCENT alone is restricted to 0 through 500;
- a typed 1-based borderFill reference, four signed offsets, connect and ignore-margin switches.

The exact child order is alignment, heading or heading switch, break settings, automatic spacing,
the 2016 HwpUnitChar layout switch, then paragraph border. Current and fallback layouts are both part
of semantic identity. Dropping or flattening either branch is forbidden.

## Border/fill profile

BorderFill models exact 1-based dense IDs, 3D/shadow/broken-cell switches, the dedicated
NONE/VERTICAL/HORIZONTAL/CROSS center-line enum, slash/back-slash geometry, five LineType2 borders,
all sixteen Appendix-F line widths and RGB colors. The current executable fill slice supports absent
fill or exactly one core winBrush with optional hatch color/style and bounded byte alpha. A hatch
style requires a hatch color; the observed 2020 hatch color without a style remains valid.

Appendix-F gradation and image-brush alternatives are structurally known but are not emitted by the
exact current fixture and are intentionally rejected as non-editable in v1. Gradation expansion needs
a separately evidenced current-runtime sample; image-brush behavior belongs with the P08 binary/image
pipeline. Unknown children or attributes inside a typed paragraph/border record reject rather than
disappear.

## IDs, semantic identity and lowering

Paragraph IDs and tab-domain IDs are dense from zero. Border, numbering and non-empty bullet domains
are dense from one. Every paragraph tab/border and NUMBER/BULLET heading reference must resolve.
OUTLINE uses the current profile's idRef zero convention; NONE also requires idRef/level zero.
P05-02 character-style border references can be checked explicitly against the same border catalog.

Paragraph semantic identity is every typed value including both compatibility branches, excluding
only the allocated paragraph ID. Deduplication retains first occurrence, reallocates dense IDs from
zero and returns a complete old-to-new map. Rewrite validates the map and source reference before
changing only P05-01 TextFlow.paragraph.paragraph_property_id_ref. No style ID, character ID, opaque
element or unrelated value is inspected or changed; failure leaves the flow unchanged.

ParagraphStyleCatalogWriter revalidates the entire public model, emits only borderFills and
paraProperties in a deterministic hh:refList, reparses it using the explicit external domains and
requires exact typed equality. The receipt records contract ID, output SHA-256, byte count,
border-fill count and paragraph-style count. Equal ordered input produces equal bytes and receipt.
The fragment does not overwrite tab, numbering or bullet definitions owned by P05-04/P05-05.

Defaults are 2 MiB input, 32,768 elements and 16,384 each for paragraph styles, border fills and
external references, with finite hard ceilings. Namespace, element/attribute shape, child order,
count, ID, reference, number, boolean, enum, color, range, input/output/model limit, allocation and
readback failures have stable fail-closed categories.

## Gate boundary

Passing P05-03 proves exact current generated-header lift, typed paragraph and referenced border/fill
semantics, both compatibility branches, cross-module border closure, deterministic dedup/reference
rewrite, lower/re-lift receipts, negative cases and a fixed synthetic 128-case layout corpus. It does
not prove arbitrary-document editing, tab/list definition semantics, page/section pagination, visual
layout, gradation/image fills, real Hangul save/render behavior, another PC, or Hangul 2022/2024.
Those claims require their later task and exact target-runtime Gates.
