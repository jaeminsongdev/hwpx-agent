# P04-02 Unit and identity policy

- Effective date: 2026-09-02
- Contract ID: `hwpx-agent.unit-id/v1`
- Implementation: `crates/domain-ir/src/units.rs`, `crates/domain-ir/src/identity.rs`

## Authoritative unit source

The conversion constant is locked to Hancom's official `HWP 5.0 revision 1.3` format document,
source ID `hancom-hwp-5-rev1.3`, SHA-256
`1d1da9e6fe22563ae2c5285bbbfc6762974fb7f002278084cbc11e5266bdc782` in
`implementation/p00/source-lock.json`. The document defines HWPUNIT/SHWPUNIT as `1/7200 inch` and
gives `2 inch x 1 inch = 14400 x 7200`; its type-size example also gives `10 pt = 1000 hwpunit`.

The older HWPML `hunit` definition of `1/1800 inch` is a distinct legacy source unit. It MUST NOT
be passed to the v1 `HwpUnit` API or silently multiplied. A future legacy importer must declare the
legacy unit explicitly and emit a separate conversion receipt.

## Canonical representations

- Layout length: `LengthMicrometers(i64)`.
- Typography: `PointMilli(i64)`.
- Ratio/percent: `RatioMillionths(i64)` where `100% = 1_000_000`.
- Angle: `AngleMicrodegrees(i64)`.
- Backend lowering unit: `HwpUnit(i64)`, `1/7200 inch`.
- Z-order: sparse signed `ZOrder(i64)`; contiguous backend IDs are not part of this contract.

Canonical equality, ordering, hashing and serialization use only integers. Binary floating-point is
not an accepted core input, so NaN and infinity are structurally unrepresentable. API adapters that
receive a JSON number must first create a bounded exact `RationalInput`; they MUST reject a value
that cannot be represented under that contract.

## Exact factors and rounding

All factors are evaluated with checked `i128` intermediates and rounded once to the target integer:

| Conversion | Exact factor |
|---|---|
| mm -> um | `1000/1` |
| pt -> um | `3175/9` |
| HWPUNIT -> um | `127/36` |
| um -> HWPUNIT | `36/127` |
| px@dpi -> um | `25400/dpi` |
| pt -> PointMilli | `1000/1` |
| ratio -> millionths | `1000000/1` |
| percent -> ratio millionths | `10000/1` |
| degree -> microdegree | `1000000/1` |

Ties use half-away-from-zero, never banker's rounding. Every conversion returns a
`ConversionReceipt` containing source/target unit, exact rational source, normalized value,
reduced signed rounding delta and optional DPI. Debug output redacts numeric values; serialized
receipts may be stored only in an evidence object with the normal content/privacy policy.

`RationalInput` denominator is `1..=1_000_000_000`. DPI is `1..=1_000_000`. Invalid bounds and all
arithmetic overflow return stable `unit_*` errors without wrapping or saturation.

## Coordinate contract

Every `Position2D` has integer micrometer x/y, a `CoordinateSpace` and a compatible
`CoordinateAnchor`:

| Space | Required anchor |
|---|---|
| `page` | `page` |
| `content` | `content` |
| `anchor` | logical node |
| `object_local` | object logical node |

Construction and deserialization both enforce the pair. Translation is checked and keeps the same
space/anchor. Implicit operations between spaces are not provided.

## Typed identities

`ProjectId`, `RevisionId`, `ArtifactId`, `LogicalNodeId`, `StyleId`, `ResourceId`, `BookmarkId`,
`FieldId`, `ChangeId` and `BackendOpaqueId` are distinct transparent newtypes. Each is non-empty,
contains no control character and is at most 512 UTF-8 bytes. Parsing and deserialization share the
same validator. Debug output is redacted and no `Display` implementation is provided.

`BackendOpaqueId` is valid only inside a source binding/anchor. It is never a logical identity and
must not cross an API or log as a backend action, numeric ID, path or raw XML value.

## Compatibility and verification

P04-02 adds types and does not change P04-01 `DocumentGraph` v2 canonical bytes. The v2 golden
digest must remain `2ab9ffef0263e14609afa148e412ba2915820e54e365c9a420c734f908a6f3c6`.

Required evidence is Windows/Linux tests and Clippy, official constants, positive/negative tie
symmetry, A4 compatibility (`210 mm -> 59528 HWPUNIT`), 10,000 fixed-seed HWPUNIT round trips,
overflow/invalid deserialization, typed-ID/redaction and coordinate-anchor cases. This task does not
run Hancom or access a user document.
