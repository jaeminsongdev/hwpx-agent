# P05-02 character-style policy

- Contract: hwpx-agent.character-style/1
- Runtime profile: licensed current-PC Hangul 2020 11.0.0.9136 x86
- XML namespace: http://www.hancom.co.kr/hwpml/2011/head
- Implementation: hwpx_package::character_style

## Source and runtime boundary

The structural source is the locked official KS X 6101 reform-03 machine response,
ks-x-6101-machine-content-20260901, SHA-256
c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4. Appendix C defines
Header XML and Appendix F supplies shared XML types and bounds. Those 2024 standard records are a
structural cross-check only. They do not prove that this PC's Hangul 2020 implements every later
version feature.

The executable profile is the exact 2011 head namespace and header.xml emitted by the P04-09 VS-0
builder, previously opened by the current licensed Hangul 2020. P05-02 regression tests read that
exact generated header: seven language groups in HANGUL, LATIN, HANJA, JAPANESE, OTHER, SYMBOL, USER
order, two dense font IDs in each group, and seven dense character-property IDs. No installed-font
enumeration, user document, arbitrary path, font substitution service, or Hangul UI is an input.

## Typed model and identity

CharacterStyleCatalogReader accepts a bounded full hh:head or standalone hh:refList only after P03
preserving XML admission. It lifts the one fontfaces and one charProperties child. Other full header
sections stay outside this targeted non-mutating view; unknown children or attributes inside the two
typed sections reject rather than disappear.

Each language group has its own dense font-ID domain. A font record types its face name, REP/TTF/HFT
kind, embedded flag, optional binary reference, optional substitute font and optional classification
record. Face names and binary references are bounded semantic strings and are escaped on output.
Debug output exposes only string length/presence, never those values.

A character style types:

- seven language-local font references;
- HWPUNIT height in the current profile range 1 through 100000;
- ratio 50 through 200, spacing -50 through 50 and relative size 10 through 250 for every slot;
- offset -100 through 100 for Hangul/Latin/Hanja and -100 through 50 for the remaining slots;
- font-spacing and kerning switches, emphasis mark, text/shade colors and external border-fill ID;
- italic, bold, underline, strikeout, outline, shadow, emboss, engrave, superscript and subscript.

RGB colors use exact #RRGGBB; none is accepted only where the current profile permits no shade.
Shadow offsets are -100 through 100. Superscript and subscript cannot both be enabled. Missing effect
children normalize to the exact current defaults, while the deterministic writer emits explicit
underline, strikeout, outline and shadow defaults.

Style semantic identity is every typed property except its allocated id. Deduplication retains the
first occurrence, assigns dense IDs from zero and returns an old-to-new mapping. Its two-pass text
rewrite first validates every typed reference, then changes only run charPrIDRef and text-span
charStyleIDRef; opaque elements are neither inspected nor rewritten. Failure leaves the flow
unchanged.

## Lowering, receipts and failure policy

CharacterStyleCatalogWriter revalidates the entire publicly mutable catalog, emits a deterministic
standalone hh:refList fragment, reparses it and requires exact typed equality. The accompanying
receipt contains the contract ID, output SHA-256, output byte length and font/style counts. Equal
ordered input produces equal bytes and equal receipts.

The fragment deliberately contains only fontfaces and charProperties. Font references are closed
against their matching language group. Binary-item and border-fill IDs are retained as typed external
references; their package-wide closure remains P03 IdIndex responsibility when the fragment is
integrated into a complete header. The writer accepts no raw XML, CSS, path, installed-font lookup,
platform fallback, COM/HAction identifier, partial output, or best-effort repair.

Defaults are 2 MiB input, 32,768 elements, 4,096 fonts per language, 16,384 styles and 4 KiB per
string. Absolute ceilings are finite. Counts, dense IDs, namespace, attribute/child sets and order,
references, enums, colors, numbers, booleans, ranges, output size, allocation and readback mismatch
have stable fail-closed error categories.

## Gate boundary

Passing P05-02 proves the exact current generated 2020 header lift, bounded typed character-style
model, semantic deduplication, typed reference rewrite, deterministic lower/re-lift and receipt,
negative cases and fixed synthetic variation corpus. It does not prove installed-font availability or
substitution behavior, visual fidelity, arbitrary existing documents, paragraph/page/section styles,
Hangul save/render behavior, another PC, or Hangul 2022/2024 compatibility. Those claims require their
later target-runtime Gates.
