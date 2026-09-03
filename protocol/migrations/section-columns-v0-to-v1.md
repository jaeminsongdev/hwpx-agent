# Section/columns v0 to v1

`hwpx-agent.section-columns/1` introduces the first typed section/column boundary. No earlier wire
shape is accepted or silently upgraded.

## Additive model

- ordered section parts and explicit boundaries between adjacent sections;
- ordered column-layout spans within each section;
- typed newspaper, balanced-newspaper, and parallel flow;
- typed left, right, and mirrored layouts;
- equal column count/gap or an exact ordered custom width/gap partition;
- optional typed separator style, width, and 24-bit RGB color; and
- deterministic lower/patch receipts with bounded metrics and source/output SHA-256 identities.

## Rejection behavior

Unknown fields, raw XML, implicit section-break policy, guessed page-side starts, floating-point
sizes, unbounded identifiers, unsupported namespaces, misplaced controls, inconsistent equal/custom
records, under-width or overflowing columns, incomplete body partitions, over-limit sequences, and
missing patch ordinals are rejected. Callers must resolve the typed error and submit an explicit
version-1 request; there is no lossy v0 fallback.
