# PackageGraph contract migration: v0 to v1

## Status

- Migration: initial contract introduction
- Producer: `hwpx-package` P03-02
- Compatibility: fail closed; there is no accepted v0 graph payload

## v1 contract

`PackageGraph::build` consumes a mutable, previously validated `BoundedZipReader` and validated `PackageGraphLimits`. It returns a complete in-memory graph only after:

- exact first/stored HWPX `mimetype` validation;
- required container/version/rootfile checks;
- bounded OCF container and OPF manifest/spine parsing;
- source-relative internal target resolution;
- manifest ID/target and spine reference uniqueness;
- existing-target and all-part closure checks;
- integrity read and SHA-256 capture for every non-directory part.

The v1 public values are `PackageGraph`, `PartRecord`, `Relationship`, `MediaType`, `PartRole`, `RelationshipKind`, `PackageGraphLimitConfig`, `PackageGraphLimits` and `GraphError::code()`.

## Failure semantics

All failures publish a stable non-sensitive code. Untrusted XML, relationship text and local paths are not included in error messages. Underlying P03-01 failures retain their existing `PackageError::code()` through `GraphError::Package`.

v1 blocks external relationships, package-root escape, DTD/custom-entity/processing-instruction/CDATA metadata, malformed namespace/media type, duplicate normalized target, dangling spine reference, missing target and orphan part. Only XML predefined and valid numeric character references are accepted. It never returns a partial graph.

## Upgrade rule

No v0 value can be upgraded implicitly because no prior graph contract existed. Callers must open the archive with P03-01 and build a fresh v1 graph. A later schema that accepts external targets, embedded HWPX packages, additional OCF infrastructure, alternate namespace semantics or lazy/unverified parts must use a new version and new negative corpus; it cannot reinterpret a v1 pass.
