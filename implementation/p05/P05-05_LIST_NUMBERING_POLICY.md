# P05-05 list and numbering policy

- Contract: hwpx-agent.list-definition/1
- Runtime profile: licensed current-PC Hangul 2020 11.0.0.9136 x86
- Head namespace: http://www.hancom.co.kr/hwpml/2011/head
- Paragraph namespace: http://www.hancom.co.kr/hwpml/2011/paragraph

## Sources and executable boundary

The locked KS X 6101 reform-03 machine-readable response is the authoritative structural source.
Appendix C defines numberings, bullets, NumberingType, BulletType and ParaHeadType. The locked source
describes one-based definition IDs, per-level numbering starts and templates, paragraph-head alignment,
width/offset behavior, number formats, character-style references and checkable bullets. The Apache-2.0
Hancom OWPML model at commit 1453388472c703a4b299a0834f425cdac16644b9 is a secondary implementation
cross-check for the same element and attribute shapes.

The executable baseline is the exact current generated Hangul 2020 header: one numbering definition
with ID 1 and start 0, exactly ten paraHead levels numbered 1 through 10, no bullets, and a section
outlineShapeIDRef of 1. Paragraph heading levels are zero-based; OUTLINE uses idRef 0 and resolves its
definition only through the section outline binding. NUMBER and BULLET use one-based definition IDs.
A shared namespace or later standard/model does not qualify another Hangul release.

No user document, arbitrary path, installed-style enumeration or unverified cross-version input is used.

## Typed definitions

ListDefinitionCatalog contains one-based dense numbering and bullet definition domains. A numbering
definition has a signed non-negative definition start and exactly ten ordered NumberingLevel records.
Each level has a one-based XML level, non-negative start, LEFT/CENTER/RIGHT alignment, explicit
useInstWidth and autoIndent flags, signed widthAdjust, PERCENT/HWPUNIT text offset, a typed number
format, a character-style reference or the exact UINT32_MAX no-style sentinel, checkable state and an
escaped template string. Templates are data only; they never become XML or backend commands.

A character bullet preserves char, optional checkedChar, useImage=false and one ParaHead style without
a numbering start. Empty or multi-scalar bullet marks, checked state without checkedChar, image-bullet
children and unresolved character-style references reject. Image bullets are intentionally deferred to
P08, where binary-item ownership and package relationship closure can be validated together.

Definitions are bounded and unknown typed children/attributes reject. Container counts, exact child
order/cardinality, dense IDs, levels, lexical numbers/booleans/enums, character references, templates
and finite input/output/model limits are validated before publication.

## Paragraph bindings and outline resolution

P05-03 Heading remains the only paragraph-style binding. NONE requires idRef/level 0; OUTLINE requires
idRef 0 and a valid section outline numbering ID; NUMBER and BULLET require an existing one-based typed
definition. Heading levels are zero-based 0..9 and map to XML paraHead levels 1..10. Deduplication
returns complete one-based old-to-new maps and atomically rewrites only typed NUMBER/BULLET paragraph
heading references. It separately remaps the section outline definition ID. All source domains, maps
and references are validated before any mutation.

## Sequence, nesting, continuity and restart

The pure ListSequenceEngine takes an explicit nonzero sequence ID, typed kind/definition binding,
zero-based level, optional nonzero restart value and bullet checked state. Sequence identity is separate
from visual definition identity so two lists using the same shape cannot accidentally share counters.
NUMBER and OUTLINE maintain ten checked u32 counters; BULLET emits no counter. A numeric sequence must
start at level 0, may increase by at most one level, may decrease to any ancestor, and may continue at
the same level. Entering a child initializes that level from its definition start; continuing or
returning to a level increments it; restart installs the explicit value and clears deeper levels. A
definition, kind or sequence mismatch is a separate stream, not implicit continuation.

Each evaluated item records its complete active counter path, whether restart was applied and the
preserved level template/format. The engine does not synthesize glyphs or claim rendered markers;
Hangul remains the renderer. Overflow, missing ancestor, zero sequence ID, invalid restart, invalid
level transition, unsupported checked bullet and all dangling definitions fail closed.

## Deterministic lowering and limits

Semantic definition identity excludes only allocated ID. Deduplication keeps first occurrence, emits
dense IDs and complete maps. The writer revalidates the public model and explicit character-style
domain, emits deterministic escaped refList XML, reparses it for exact typed equality and returns
profile, SHA-256, bytes and definition/level counts. Raw XML, arbitrary paths, COM/HAction names and
platform guesses are outside the public contract.

Defaults are 2 MiB input, 32,768 elements, 4,096 numbering definitions, 4,096 bullet definitions,
40,960 levels, 65,536 sequence items, 65,536 paragraph/reference items and 256 UTF-8 bytes per
template or bullet mark, with finite hard ceilings.

## Gate boundary

Passing the pure package slice proves exact generated-header readback, bounded character-bullet and
numbering definitions, paragraph/outline reference closure, semantic dedup/rewrite, deterministic
lower/re-lift and explicit sequence/nesting/continuity/restart counters. The disposable exact Hangul
2020 fixture must then prove that this build accepts and preserves the selected NUMBER, BULLET and
OUTLINE shapes through save/reopen. This task does not prove image bullets, arbitrary-document editing,
rendered glyph/layout fidelity, pagination, another PC or Hangul 2022/2024.
