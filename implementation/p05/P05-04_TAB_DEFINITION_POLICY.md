# P05-04 tab-definition policy

- Contract: hwpx-agent.tab-definition/1
- Runtime profile: licensed current-PC Hangul 2020 11.0.0.9136 x86
- Head namespace: http://www.hancom.co.kr/hwpml/2011/head
- Compatibility namespace: http://www.hancom.co.kr/hwpml/2011/paragraph

## Sources and executable boundary

The locked KS X 6101 reform-03 machine-readable response is the authoritative structural source.
Appendix C defines tabProperties, TabDefType and tabItem; Appendix F defines LineType2. The standard
defines non-negative tab IDs, boolean automatic-left/right flags, signed integer HWPUNIT positions,
LEFT/RIGHT/CENTER/DECIMAL alignment and the twelve LineType2 leader values. The current exact generated
header is the executable baseline: three dense definitions with no custom stops and automatic flag
pairs 0/0, 1/0 and 0/1.

The Apache-2.0 Hancom OWPML model at commit 1453388472c703a4b299a0834f425cdac16644b9 is a secondary
implementation cross-check. It confirms repeated child storage and an optional CHAR/HWPUNIT unit field,
but its extra VERTBAR and legacy line variants are not promoted into this current-2020 contract without
target evidence. Public third-party reports of HwpUnitChar switch pairs are treated only as test-design
clues. They do not qualify runtime behavior; this PC's disposable target readback must do that.

No user document, arbitrary path, installed-style enumeration or unverified cross-version input is used.

## Typed model and preservation

TabDefinitionCatalog contains dense zero-based definitions. Each definition preserves automatic left
and right flags and a strictly increasing ordered stop list. A direct stop preserves non-negative signed
position, one of four alignments, a LineType2 leader and an optional CHAR/HWPUNIT unit attribute.
Omitted units mean HWPUNIT. Stops within one definition must share one effective unit so numeric order
is never guessed across incomparable coordinate systems.

The exact-current compatibility form is represented separately as HwpUnitChar { current, fallback }.
It preserves both tabItem branches instead of collapsing them. The current branch requires HWPUNIT,
the fallback branch requires an omitted unit, type and leader must match, and the fallback position must
equal current times two or current times two plus one. The fallback value is the effective ordering key,
so odd positions remain lossless. Unsupported switch namespaces, branch shapes or inconsistent pairs
fail closed.

IDs, counts, element/stop totals, namespaces, attributes, numeric and boolean lexical forms, enums,
non-negative positions and strict order are validated. Unknown typed children or attributes reject.
The default limits are 2 MiB input, 32,768 elements, 16,384 definitions and 65,536 stops, with finite
hard ceilings.

## Deduplication and references

Semantic identity is all automatic flags and the exact ordered stop representation, excluding only the
allocated definition ID. Deduplication keeps first occurrence, allocates dense IDs and returns a complete
old-to-new map. Paragraph rewrite first validates the entire public map, old external tab domain and all
source tabPrIDRef values; it then changes only typed P05-03 references and installs the new dense domain.
No partial mutation or opaque-ID rewrite is allowed.

The writer revalidates the public model, emits deterministic refList XML, reparses it for exact typed
equality and returns profile, SHA-256, bytes, definition count and conceptual stop count. Raw XML,
arbitrary paths, COM/HAction strings and platform guesses are outside the public contract.

## Gate boundary

Passing the package slice proves exact generated-header readback, bounded typed automatic/custom tab
semantics, direct and compatibility preservation, dedup/reference rewrite, deterministic lower/re-lift,
negative cases and a fixed synthetic corpus. It does not prove that this Hangul 2020 build accepts and
canonicalizes every custom shape. That claim requires the disposable target readback in this task. It
does not prove arbitrary-document editing, visual alignment, tab behavior inside tables/columns, another
PC or Hangul 2022/2024.

## Exact Hangul 2020 save canonicalization

The disposable current-PC target fixture deliberately writes one valid odd HwpUnitChar fallback pair
(`current * 2 + 1`). Licensed Hangul 2020 build 11.0.0.9136 accepts the package and, on HWPX SaveAs,
canonicalizes that fallback from 4001 to 4000 while preserving the current position, alignment, leader,
paragraph tab reference and visible-text digest. The target inspector therefore compares the saved file
against this one explicit observed canonical form. The public reader/writer still preserves either valid
input pair exactly; it does not silently apply an application-side normalization or infer behavior for
another build.
