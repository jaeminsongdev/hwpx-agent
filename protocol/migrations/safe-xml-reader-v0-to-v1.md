# Safe XML reader contract migration: v0 to v1

## Status

- Migration: initial reusable safety-layer introduction
- Producer: `hwpx-package` P03-03
- Consumer: P03-02 container and OPF graph parser
- Compatibility: fail closed; no accepted v0 safe XML document existed

## v1 contract

v1 parses bounded UTF-8 XML 1.0 into crate-internal structured events only. It enforces one root, a first-position declaration, matching markup, namespace URI resolution, literal and expanded attribute uniqueness, finite input/event/node/depth/text/attribute/namespace limits and fallible event publication.

The public diagnostic surface is `SafeXmlError::code()`. The parser, limits, attributes and event document remain internal and cannot be used as a raw XML or resolver capability by public/LLM paths.

## Failure semantics

v1 rejects DTD, custom entity, processing instruction, CDATA, XML 1.1, non-UTF-8 declarations, invalid namespace, unknown prefix, duplicate expanded attribute, multiple root and every configured limit violation. XML predefined and valid numeric character references are the only entity-like references accepted.

All failures are deterministic and do not include untrusted XML text. No partial safe document is returned.

## PackageGraph adoption

The previous P03-02 narrow container/OPF loops are removed. Both consumers now parse through v1, then apply their existing HWPX structural rules over safe structured events. Safe XML failures are mapped to the pre-existing PackageGraph v1 error families, so the PackageGraph contract does not require a version bump.

## Upgrade rule

There is no implicit v0 upgrade. Any later change that exposes raw text, permits DTD/custom entities/CDATA/processing instructions, accepts XML 1.1/legacy encodings, enables external resolution or raises hard ceilings requires a new version, policy review and new bomb/network/filesystem negative corpus.
