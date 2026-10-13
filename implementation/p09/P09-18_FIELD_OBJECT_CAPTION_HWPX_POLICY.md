# P09-18 object-bound caption number composition

## Admitted profile

The existing caption of one selected native object is the only writable scope.
`FieldObjectCaptionHwpxTarget` binds a logical object ID, a unique native `u32` ID,
and `Picture`, `Table` or `Equation` kind. The object must be a paragraph-namespace
direct run child, have matching `numberingType` and `lock="0"`. Picture admission
includes `pic`, `rect`, `ellipse`, `line`, `arc`, `polygon`, `curve`, `connectLine`.
Table is `tbl`; equation is `equation`. A table does not require an invented `instid`.

Exactly one direct `caption` and its one direct `subList` are required. Caption
creation, locked objects, non-DIGIT fields, more than one field, and local ancestor
namespace declarations are rejected. The caller supplies the complete paragraph
map for this caption and its complete field state, not a partial caption inventory.

## Composition, binding and preservation

An exact caption-content view inherits the source section root. P09-16's existing
sealed numeric field builder/reader/lowerer runs on that view. This is composition,
not a second parser or a new native field representation. Source section, object,
caption, selector, domain state/flow/map, styles and both plan hashes are bound.

Insertion changes one verified `ctrl/autoNum` wrapper; numeric update changes only
the verified `num` attribute. The caption splice rechecks all outer bytes and reads
the target projection back. Failures return no output and no fallback. Inherited
finite state/XML/plan/output limits apply. Debug output redacts content/bindings.
Logical IDs and cached numeric results come from caller-verified context; this
adapter does not derive a document-wide sequence or prove application recalculation.

## Evidence boundary

The official OWPML model is pinned at `1453388472c703a4b299a0834f425cdac16644b9`.
Shared object attributes, caption/subList relation, ten concrete object caption
routes and DIGIT auto-number shape are source-qualified. That source does not
establish exact-target recalculation or a complete native object corpus.

Current tests use synthetic object shells, not complete native objects or packages.
`actual_hangul=false`, `semantic_save_reopen=false`, `render=false`,
`differential=false`, `green_rows=0`, `p09_complete=false`, `product_complete=false`.
REF-008/009 remain static integration/non-green. The P09-17 failed predecessor and
all private receipts remain immutable; P08/P17 source authorities are not refreshed.

## Next target boundary

Construct disposable complete-object fixtures through source-qualified object
adapters or exact captured seeds, with caption field state and independent expected
application numbering. Then require real save/reopen, semantic/render and differential
evidence. Stop and pause before a new access-allow interaction as requested by the
user; do not launch COM or automate Hangul UI to cross that boundary.
