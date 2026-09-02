# P03-05 Part preservation map policy

- State: implemented for synthetic current-PC local core validation
- Product boundary: complete evidence-ranked classification of a closed HWPX graph
- Inputs: bounded ZIP reader, supplied `PackageGraph`, validated graph limits
- Consumer: P03-06 reference index and later P03 patch/writer/diff tasks

## 1. Trust and completeness

`PreservationReport` does not trust public `PackageGraph` fields by themselves. It rebuilds an authoritative graph from the same bounded reader, compares package document, relationships, spine and per-path media/role/size semantics, then re-reads every non-directory part.

Every supplied graph part must map to exactly one portable collision key in the bounded reader. Missing, extra, duplicate or semantically changed graph parts fail the entire build. Each readback must match graph expanded size and SHA-256. A hard mismatch returns no partial report.

Report records are sorted by canonical `PackagePath`, independent of caller vector order. Every record also retains source ZIP entry index, compression method, compressed/expanded size and CRC32 so deterministic classification does not erase original order/compression evidence.

## 2. Preservation classes

| Class | Automatic v1 assignment | Required evidence |
|---|---|---|
| `ByteExact` | exact root `mimetype` only | P03-02 first/stored/exact value contract plus raw identity readback |
| `TokenStable` | XML-path and XML-media part accepted by P03-04 | safe XML admission, complete token/tree, internal byte/SHA untouched verification |
| `Semantic` | never automatic in v1 | future explicit semantic parser/comparator evidence |
| `Regenerated` | never automatic in v1 | future product-owned normalized producer evidence |
| `Opaque` | non-XML part with matched supported signature, or unrecognized non-XML media without XML-looking content | raw identity; no semantic claim |
| `Rejected` | unsafe XML, XML path/media mismatch, XML-looking content under non-XML media, supported binary signature mismatch | stable policy reason; blocks direct-preserve candidate readiness |

`Opaque` means uninterpreted bytes are inventoried for future byte copy. It does not claim the media payload is semantically valid. `direct_preserve_ready=true` means classification has no `Rejected` part; it does not claim that the P03-08 writer exists.

## 3. XML and media policy

XML media is `*/xml` or a subtype ending `+xml`. XML path hints are `.xml`, `.hpf`, `.opf`, `.rels`, `.xsd`, `.svg` and the current-2020 container metadata suffix `.rdf`, compared case-insensitively. A one-sided media/path hint is rejected rather than guessed.

An XML candidate is parsed only by `PreservingXmlDocument`. P03-03 safety rejection becomes a complete `Rejected` record with the existing stable `safe_xml_*` code. Token/span/tree/allocation or untouched-equality failures after safe admission are internal hard errors, not content downgrades.

For non-XML media, UTF-8 BOM/XML-whitespace followed by `<` is treated as XML-content/media mismatch. Supported bounded signature checks are PNG, JPEG, GIF, WebP, BMP, PDF, TrueType and OpenType. A mismatch is `Rejected`; a match remains `Opaque`. Other media remain `OpaqueUnrecognizedMedia` only when they do not look like XML.

## 4. Record and diagnostics surface

Each `PartPreservationRecord` contains only:

- canonical package path, media type and graph role;
- source entry index, compression, compressed/expanded size and CRC32;
- raw SHA-256;
- class and stable reason;
- for `TokenStable`, token/element counts, source SHA-256 and untouched-verified flag.

No part bytes, XML text, attribute values, comment/entity content, filesystem path or resolver capability is published. Unsafe XML reasons reuse stable policy codes and never include the rejected fragment.

## 5. Failure and compatibility

Hard report errors are bounded package failure, authoritative graph rebuild failure, graph-shape mismatch, raw identity mismatch, internal token-model failure and allocation failure. Content policy failures stay visible as `Rejected` records so the report remains complete and auditable.

P03-01 through P03-04 APIs remain compatible. `PackageGraph` semantics are revalidated rather than changed. `Semantic` and `Regenerated` are reserved enum values; using them automatically requires a new evidence policy and migration.

This task is synthetic package evidence. It does not prove an actual user HWPX class map, modified-part serialization, byte-exact ZIP copy, 한글 2020 round trip or other-version behavior.
