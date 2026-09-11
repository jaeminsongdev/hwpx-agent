# P08-01 asset pipeline report

## Result

Result: `component_pass / target_not_run`.

The first P08 implementation checkpoint adds a fail-closed embedded-image asset store adapter in
`hwpx-package`. It reuses the existing closed package graph and preserving patch transaction rather
than introducing a second ZIP or relationship writer.

## Implemented evidence

- Five canonical image media types are sniffed and structurally parsed with exact dimensions.
- PNG validates ordered chunks and CRC; JPEG requires a frame, scan and terminal marker; GIF walks
  color tables, extensions, image blocks and trailer; WebP validates RIFF/chunks and dimensions;
  BMP validates headers, encoding and uncompressed pixel extent.
- Complete payload SHA-256 drives deterministic full-digest IDs and `BinData` paths.
- Existing content deduplicates only through one consistent manifest relationship; ambiguous,
  media-conflicting, ID-colliding and part-colliding states reject.
- The ordered source package graph is bound at plan and lowering time. Strict private plan reload
  also rechecks its raw digest, payload, dimensions, dedup decision and semantic plan digest.
- New part plus relationship patching is atomic, preserves all other parts, and passes the existing
  package writer's closed reopen verification. Debug output is redacted.

Focused Rust tests: 10/10 PASS. They cover all five media, malformed/truncated/mismatched payloads,
byte/dimension/pixel/inventory limits, deterministic plans, strict JSON and tamper rejection,
source drift, reuse, relationship ambiguity, digest/media conflicts, deterministic collisions,
atomic part/relationship addition, writer reopen and stable error codes.

## Evidence boundary

The passing writer-reopen test is a synthetic HWPX package graph without a drawing object. It proves
the P08-01 asset/relationship transaction and package trust chain only. It is not an image-insert,
actual Hangul, visual, render or P08 phase Gate.

`actual_hwpx_image=false`, `actual_hangul=false`, `save_reopen=false`, `render=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false` remain explicit.

## Next exact task

Implement P08-02 image insertion at `max`: typed embed-only image request, drawing-control lowerer,
complete object/asset/relationship/anchor/flow state binding, strict static reopen, preservation and
target fixtures. Linked fetching remains fail-closed until its separate allowlist/security policy.
