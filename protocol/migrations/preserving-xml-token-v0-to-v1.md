# Preserving XML token contract migration: v0 to v1

## Status

- Migration: initial exact-source token model introduction
- Producer: `hwpx-package` P03-04
- Consumer: P03-05 preservation map and later P03 patch/writer tasks
- Compatibility: additive; no v0 token document existed

## v1 contract

v1 admits only P03-03 safe UTF-8/XML 1.0 and owns an immutable private source copy. It publishes checked original-coordinate byte spans, structural token kinds, namespace-resolved name metadata, ordered attribute metadata and a deterministic parent/child/sibling element index.

Every published token sequence covers the original bytes exactly once and in order. UTF-8 BOM is an explicit token. Start/end/empty markup, text, XML whitespace, predefined/numeric reference spelling and comments retain exact source slices. Attribute order and quote style are preserved; attribute values and raw text are not exposed through the public model.

## Untouched verification

The internal v1 serializer concatenates token slices without decoding or re-encoding. The public `verify_untouched_round_trip()` operation requires byte equality and SHA-256 equality but returns no raw XML. The document's `Debug` representation is summary-only.

## Failure semantics

P03-03 safety codes remain authoritative for unsafe input. v1 adds deterministic codes for invalid spans, token/source mismatch, invalid tree, allocation failure and untouched equality drift. Failures contain no untrusted XML and return no partial model.

## PackageGraph compatibility

PackageGraph continues to consume the P03-03 events and stable graph error families. Safe events now carry parallel internal source spans and ordered attribute-name metadata so P03-04 can build its model without a second semantic parse; this is not a public PackageGraph version change.

## Upgrade rule

A future change that exposes raw source/value/comment content, enables arbitrary rewrite or resolver capability, changes half-open source coordinates, normalizes untouched bytes, weakens P03-03 admission, or raises hard ceilings requires a new contract version, migration and negative corpus review.
