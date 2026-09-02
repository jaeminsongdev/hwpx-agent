# Preservation report contract migration: v0 to v1

## Status

- Migration: initial per-part preservation report introduction
- Producer: `hwpx-package` P03-05
- Consumer: P03-06 and later P03 preserving editor/writer/diff tasks
- Compatibility: additive; no v0 preservation report existed

## v1 contract

v1 rebuilds an authoritative closed graph, verifies the supplied graph snapshot, re-reads every non-directory part through the bounded reader and requires exact expanded size/SHA-256 identity before publishing a deterministic canonical-path-sorted report.

Records include package identity/role, source entry order and compression evidence, CRC32, SHA-256, class, stable reason and optional non-sensitive token counts. Raw bytes and XML values are not part of the contract.

## Class semantics

v1 automatically assigns only:

- `ByteExact` to the exact HWPX `mimetype` contract;
- `TokenStable` to P03-04-admitted and untouched-verified XML;
- `Opaque` to non-XML bytes without a contradiction;
- `Rejected` to unsafe XML, XML/media/path contradiction or supported binary-signature mismatch.

`Semantic` and `Regenerated` are reserved and always have zero automatic count. They require later explicit producer/comparator evidence.

The XML path allowlist includes `.rdf` because current 한글 2020 declares `META-INF/container.rdf` as an ancillary `application/rdf+xml` rootfile. Other one-sided media/path hints remain rejected.

## Readiness and failure

One `Rejected` record makes `direct_preserve_ready=false` but does not hide other records. Reader/graph set drift, graph semantic mutation, raw size/hash drift, internal token failure or allocation failure aborts without a partial report.

Stable reason/error codes contain policy identifiers only. P03-03 safe XML failure codes are preserved for rejected XML.

## Upgrade rule

Changing automatic class promotion, accepting path/media mismatch, downgrading unsafe XML to opaque, exposing raw content, omitting authoritative graph/readback verification, treating readiness as writer completion, or widening supported signature semantics requires a new version and migration.
