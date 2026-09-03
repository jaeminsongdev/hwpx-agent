# P05-01 text-flow policy

- Contract: `hwpx-agent.text-flow/v1`
- Runtime profile: licensed current-PC Hangul 2020 `11.0.0.9136` x86
- XML namespace: `http://www.hancom.co.kr/hwpml/2011/paragraph`
- Implementation: `hwpx_package::text_flow`

## Source boundary

The structural source is the locked official KS X 6101 reform-03 machine response,
`ks-x-6101-machine-content-20260901`, SHA-256
`c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`. Appendix E,
record 466, defines paragraph runs, mixed text, tabs, line breaks and field boundaries in the 2024
standard namespace. It is used only as a structural cross-check. It does not prove that the current
Hangul 2020 installation emits the 2024 namespace or every 2024 shape.

The executable profile is therefore the exact 2011 paragraph namespace observed in the P04-09
current-PC VS-0 artifact and opened/read back by Hangul 2020. P05-01's regression lifts that generated
paragraph, including its layout elements as opaque records. No user document or private source is an
input to this task.

## Typed contract

`TextFlowReader` accepts one bounded standalone `hp:p` through the P03 preserving XML parser. It
types paragraph identifiers/flags, ordered runs, ordered text spans, Unicode text, `tab`, `lineBreak`,
and exact nested/sequential `fieldBegin`/`fieldEnd` boundaries. Run and text-span boundaries are not
merged. Field IDs are unique within the flow, ends must close the active begin, and the field-type set
is the locked standard enumeration.

Unimplemented non-text elements become immutable `OpaqueTextElement` metadata containing only
namespace/name accessors, a source digest, byte length and a conservative visible-text flag. Raw XML
is not retained in or exposed by that object. Known current-profile layout elements (`secPr`, `colPr`,
`linesegarray`, `lineseg`) do not contribute semantic text. Every other opaque element, including a
lookalike from another namespace, blocks complete visible-text extraction. Debug output redacts text,
field names and opaque names/content.

`visible_text_nfc` is a comparison view only: it maps typed tabs and line breaks to `\t` and `\n` and
returns NFC without changing stored Unicode scalars or source boundaries. It fails closed when opaque
content may contain visible text.

## Lowering and failure policy

`TextFlowWriter` accepts only fully typed, non-opaque values. It revalidates all publicly mutable
fields, emits deterministic escaped XML through typed values only, then reparses and requires exact
typed equality before returning bytes. There is no raw XML/action-string input, best-effort repair,
namespace fallback, partial result or silent discard.

Default limits are 2 MiB input, 4,096 runs, 16,384 counted items, 1 MiB text and field depth 128.
Absolute ceilings remain finite. Checked counters and fallible container growth produce stable error
codes for malformed preserving XML, wrong profile, unsupported shape, invalid numbers/booleans/text/
tabs/fields, duplicate/misnested/unclosed fields, limit overflow, opaque semantic/lowering refusal,
output overflow and allocation failure.

## Gate boundary

Passing P05-01 proves the bounded text-flow model, deterministic lift/lower/lift behavior, fixed
Unicode/run-boundary corpus, negative field/limit/profile cases and lift compatibility with the
current generated Hangul-2020 VS-0 paragraph. It does not prove arbitrary-document editing, character
or paragraph style semantics, tables/drawings/equations, actual Hangul-2020 field creation/readback,
save/render fidelity, another PC, or Hangul 2022/2024 runtime compatibility.
