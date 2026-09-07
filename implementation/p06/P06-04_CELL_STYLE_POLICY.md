# P06-04 Cell formatting policy

- Current exact-build contract: `hwpx-agent.table-cell-style.hancom-2020/2`
- Contract record: `protocol/private/p06-table-cell-style-v2.json`
- Immutable predecessor: `hwpx-agent.table-cell-style.hancom-2020/1`
- Implementation: `hwpx_package::TableCellStyleLowerer` and `TableCellStyleReader`
- Runtime target: this PC's licensed Hangul 2020 `11.0.0.9136` x86 installation

## Evidence and version boundary

The frozen P06 design sources define the product scope. P02's locked OWPML records and locally
cached official Apache-2.0 model source define the current `hp:tc`, `hp:cellMargin`, `hp:subList`
attributes and enum tokens. P02's automation records identify `TableCreate`, `CellBorder`,
`CellFill`, alignment, direction and vertical-alignment actions, but those records are
documentation-only and do not become a general public automation route through P06-04.

This task qualifies only the exact local Hangul 2020 build. Hangul 2022 and 2024 remain deferred
until a PC carrying those licensed versions is available; no guessed compatibility claim is made.

## Typed style and references

Margins are either absent or four unsigned HWPUNIT values under a finite configured ceiling.
The exact Hangul 2020 output can retain inherited/default nonzero margin numbers while
`hasMargin="0"` makes them semantically inactive. The v2 reader maps that form to absence, and a
v2 lowering to absence preserves the inactive numeric spans instead of inventing normalization.
The v1 default APIs retain their canonical-zero rule. Border and fill
are selected by one exact `borderFillIDRef`; it must resolve exactly once in the validated header
catalog and stay within the current implementation's unsigned 16-bit storage width.

Horizontal alignment is not a `tc` attribute. The style therefore carries both the requested typed
alignment and one exact paragraph-property ID. That ID must resolve exactly once and its catalog
alignment must equal the request. Every direct paragraph in the cell receives the same reference;
mixed source references fail closed rather than selecting the first. Vertical alignment and text
direction use only the official tokens. Protection preserves all four explicit combinations of the
independent `protect` and `editable` bits instead of inventing an undocumented dependency.

## Preserving lowerer

The observed exact-build v2 profile has exactly `subList`, `cellAddr`, `cellSpan`, `cellSz` and
`cellMargin` children in that order, and at least one direct `hp:p` child under `subList`. It also
uses the explicit table-ID v2 profile and the exact-path `Preview/PrvText.txt` text/plain
preservation rule. The immutable v1 order and preview rejection remain available through v1 APIs;
there is no auto-detection. Unknown style attributes, duplicate attributes, wrong namespaces and
malformed values reject.

Standalone-cell and full-section entry points share one implementation. The section form requires
the exact section root namespace, counts every cell under a separate finite total-cell limit, and
then selects a cell by zero-based document order. Only the existing style attribute value spans are
rewritten: `hasMargin`, four margins, `borderFillIDRef`, `protect`, `editable`, `textDirection`,
`vertAlign` and every cell paragraph's `paraPrIDRef`. Cell addresses, spans, sizes, names, IDs,
runs, text, fields and all sibling bytes are left untouched.

After editing, the output is reparsed. All typed style fields, paragraph count and a content-token
SHA-256 must match the request and pre-edit source. The receipt records only lengths, counts and
digests; it never contains cell text.

## Runtime Gate

The runtime fixture is created only from a new blank document and fixed synthetic markers. The
runner verifies the exact executable identity, requires 32-bit STA automation, explicitly activates
the exact document object before any `HAction`, and leaves the window visible for the user's
file-access approval. It verifies every marker in that active document before saving, saves HWPX,
reopens it, verifies all markers again and exports a signed PDF-shaped artifact. Product-generated
style output must then pass the same
save/reopen/readback/render sequence before P06-04 can close.

The P06-04 runtime wrapper delegates to the already qualified bounded x86 STA watchdog. It binds
the exact input digest and canonical visible-text digest, requires create-new HWPX/PDF/trace paths,
records a bounded progress journal, verifies the exact executable identity, and treats timeout,
unknown output, invalid trace, PDF mismatch or any remaining Hwp process as failure or unverified.

No user document is scanned or opened. A component test, documentation record, source fixture or
PDF signature alone is not promoted to the actual runtime PASS.

## Deferred semantics

P06-04 does not add new border-fill catalog entries, repair arbitrary table XML, evaluate formulas,
solve row/column layout, qualify general automation routing, support arbitrary user documents, prove
another PC/version, close P06, or complete the product.
