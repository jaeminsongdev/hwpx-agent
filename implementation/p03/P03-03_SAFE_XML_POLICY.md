# P03-03 Safe XML reader policy

- State: implemented for synthetic current-PC local core validation
- Product boundary: reusable internal XML 1.0 safety layer for HWPX metadata
- Consumer: P03-02 `PackageGraph` container and OPF parsers
- Parser primitive: exact-pinned `quick-xml = 0.42.0`, default features disabled

## 1. Contract and exposure

`safe_xml` owns the reusable parser, finite limits, namespace resolution and structured internal event document. The parser and its event values are crate-internal. It does not expose raw XML, text, comments, DTD data or a namespace/entity resolver through the public crate API.

`SafeXmlError` alone is public so diagnostics can retain stable non-sensitive `code()` values. Error messages contain only fixed policy names and numeric limit values; they never include XML fragments, element/attribute values, paths or entity names.

Internal start/empty events contain qualified/local names, resolved namespace URI, normalized attributes and depth. Text events expose only a byte count to the graph consumer. P03-04 must introduce a separate preserving-token contract rather than widening this safety API with arbitrary raw XML.

## 2. Accepted XML profile

- Input is strict UTF-8.
- An omitted declaration means XML 1.0. If present, the declaration must be the first parser event, declare exactly version `1.0`, optionally declare case-insensitive `UTF-8`, and use only valid `standalone=yes|no`.
- Exactly one document element is required. Non-whitespace text outside it and a second root are malformed.
- Start/end name matching and XML comment checks are enabled.
- Element namespaces are resolved by URI, not literal prefix. Descendant prefix rebinding is reflected in the structured event.
- Unknown prefixes and invalid namespace bindings fail closed.
- Attribute names are checked both by literal QName and by expanded `(namespace URI, local name)` so two prefixes cannot smuggle a duplicate attribute.
- XML's predefined `amp`, `lt`, `gt`, `apos`, `quot` references and numeric references for valid XML scalar ranges are accepted.

## 3. Forbidden capability

The following are rejected before an internal document is published:

- DTD or DOCTYPE;
- custom/general named entity;
- processing instruction;
- CDATA;
- XML 1.1 or non-UTF-8 encoding declaration;
- external entity, filesystem, network or application resolver;
- malformed/dangling markup, duplicate attribute, invalid/unknown namespace or multiple root.

The crate contains no XML-driven filesystem/network/process API. `quick-xml` performs lexical parsing and namespace resolution only; the product does not register callbacks that can fetch or expand external data.

## 4. Finite limits

| Limit | Default | Hard ceiling |
|---|---:|---:|
| input bytes | 2 MiB | 16 MiB |
| events | 100,000 | 1,000,000 |
| nodes | 100,000 | 1,000,000 |
| depth | 64 | 256 |
| one text event | 1 MiB | 16 MiB |
| total text bytes | 2 MiB | 16 MiB |
| attributes per element | 32 | 256 |
| aggregate attribute bytes per element | 8 KiB | 64 KiB |
| active namespace bindings | 2,048 | 4,096 |

Every value must be non-zero and at or below its hard ceiling. One-text limit must not exceed total-text limit, and total-text limit must not exceed input limit. Event publication and parser-owned vectors use fallible reservation where the standard library permits it.

`PackageGraph` derives its internal safe XML limits from validated `PackageGraphLimits`: metadata bytes become input/total-text bounds, events also bound nodes, text-event size is capped at 1 MiB, and active namespaces are derived from attribute/depth bounds then capped at 4,096.

## 5. Failure mapping and compatibility

Safe XML has distinct stable codes for input/event/node/depth/text/attribute/namespace limits, malformed data, forbidden constructs and allocation failure. `PackageGraph` maps them into its existing P03-02 `metadata_too_large`, `xml_limit_exceeded`, `xml_namespace_invalid`, `xml_forbidden_construct`, `xml_malformed` and `graph_allocation_failed` families. Existing P03-02 callers therefore keep their v1 graph error codes.

This task is synthetic parser evidence. It does not prove full HWPX XML vocabulary correctness, byte-preserving tokenization, an actual Hangul 2020 document, writer preservation or round trip.
