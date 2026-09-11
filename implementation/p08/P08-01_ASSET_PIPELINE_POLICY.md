# P08-01 asset pipeline policy

## Decision

P08-01 is `component_pass / target_not_run` for the finite embedded-image asset profile. The
adapter implements bounded MIME sniffing, structural media validation, SHA-256 content identity,
deterministic deduplication, package-graph binding, collision-safe part/relationship planning and
atomic integration with the preserving patch engine. It does not close P08 image insertion or any
licensed-Hangul/render Gate.

## Admitted media and identity

The v1 profile admits canonical `image/png`, `image/jpeg`, `image/gif`, `image/webp` and
`image/bmp`. Declared MIME must exactly match the sniffed format. Signature-only acceptance is
insufficient: each format's bounded container structure, dimensions and terminal records are
checked; PNG chunk CRCs are checked. Empty, truncated, malformed, unsupported, dimension-excessive
or byte-excessive payloads fail before a plan exists.

Content identity is the SHA-256 of the complete payload. New assets use a full-digest relationship
ID and `BinData` path, without a caller filename. Existing manifest-listed `BinData` content is
reused only when size, digest and media all agree and one exact package-document manifest
relationship owns the part. Ambiguous relationships or digest/media conflicts fail closed.

## Source and lowering boundary

Planning binds the complete ordered `PackageGraph`: package document, every part path/media/role/
size/raw digest, every relationship field and spine order. Immediately before producing patch
intents, the adapter recomputes that graph digest, fully rebuilds the plan from the private payload
and requires exact equality. The preserving patch engine independently rebuilds the authoritative
graph from the bounded package reader.

A new asset produces exactly one opaque `AddedPart` and one non-spine manifest
`RelationshipAddition`; the existing patch transaction requires both or neither. A reused asset
produces no duplicate part or relationship. The later P08-02 object lowerer consumes the returned
typed relationship ID and combines these intents with the drawing control in one transaction.

## Private plan and limits

The deterministic private JSON plan never embeds asset bytes. Loading requires a caller-pinned raw
plan SHA-256 and recomputes the graph, payload digest, MIME parser, dimensions, dedup selection,
path, relationship ID and semantic plan digest. Unknown, duplicate, missing, relabeled, oversized or
tampered JSON fails. Public `Debug` omits payload, relationship ID, path and all digests.

All byte, inventory, JSON, dimension and pixel limits are nonzero, finite and hard-ceiling checked.
The effective payload bound also respects the preserving patch engine's added-part limit. Allocation
failure yields no partial public plan or intents.

## Explicit non-claims

TIFF, SVG/XML images, linked-resource fetching, image decoding/pixel correctness, crop/resolution/
alt text, drawing controls, object geometry, OLE/multimedia activation and external content are not
claimed by this profile. P08-02 and P08-08 own those boundaries. No actual HWPX fixture containing
a drawing object, Hangul 2020 open/save/reopen, render, differential, P08 completion, production or
product completion is claimed.

Reasoning level: `high` for this pure bounded component; P08-02 exact HWPX lowering remains `max`.
