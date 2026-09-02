# P03-04 Preserving XML token policy

- State: implemented for synthetic current-PC local core validation
- Product boundary: exact-source token/span and lightweight tree layer over P03-03 safe XML
- Consumer: P03-05 preservation classification and later bounded patch/writer tasks
- Parser primitive: P03-03 `safe_xml` with exact-pinned `quick-xml = 0.42.0`

## 1. Admission and ownership

`PreservingXmlDocument::parse` first completes the P03-03 UTF-8/XML 1.0 validation. A token document is never returned for DTD, custom entity, processing instruction, CDATA, invalid namespace, malformed markup or a configured limit violation.

Accepted source bytes are copied into a private immutable `Box<[u8]>` only after structural validation. The public API exposes source length, SHA-256, checked spans, token kinds, namespace/name metadata and tree indices. It does not expose raw text, attribute values, comments, arbitrary XML serialization or a rewrite/resolver callback. Custom `Debug` emits only length, digest, counts and root index; it never prints source bytes.

## 2. Source coordinate contract

- Every `XmlByteSpan` is a half-open `[start, end)` byte range in the original input coordinate system.
- `start <= end <= input.len()` and both endpoints must be UTF-8 character boundaries.
- Published top-level tokens are non-empty, ordered, non-overlapping and gap-free from byte 0 through `input.len()`.
- A UTF-8 BOM is represented as a distinct `ByteOrderMark` token. The `quick-xml` BOM-relative position is corrected by three bytes before source spans are published.
- Start/end QName, attribute, attribute-name and attribute-value spans are checked independently against the source.
- Span constructors are private; callers cannot manufacture unchecked model spans.

## 3. Token and tree model

Token kinds are `ByteOrderMark`, `Declaration`, `StartElement`, `EmptyElement`, `EndElement`, `Text`, `Whitespace`, `Reference` and `Comment`. XML whitespace is exactly space, tab, CR or LF; mixed content remains `Text`. Entity spelling, quote style, whitespace, comments and prefix spelling are preserved by the immutable token slice even though their raw content is not exposed.

Each element records:

- qualified name, prefix, local name and resolved namespace URI;
- depth, matching start/end token and tag/name spans;
- checked outer/content spans;
- ordered attribute metadata and single/double quote style;
- parent, first/last child and previous/next sibling indices;
- empty-element identity.

Non-namespace attributes retain their resolved namespace identity. Default namespaces do not apply to unprefixed attributes. Namespace declarations are marked explicitly and use the standard `http://www.w3.org/2000/xmlns/` identity. The reserved `xml` prefix resolves to `http://www.w3.org/XML/1998/namespace`. Descendant prefix rebinding is resolved at each element.

## 4. Untouched reconstruction

The internal untouched serializer concatenates the exact private source slice for every token in order. It performs no normalization, decoding, entity expansion, namespace rewrite, line-ending conversion or UTF-8 re-encoding.

`verify_untouched_round_trip()` reconstructs internally, then requires both byte-for-byte equality and SHA-256 equality with the admitted source. It returns no reconstructed bytes to the public caller. A gap, overlap, invalid span, unmatched element or equality drift fails closed with a stable non-sensitive code.

## 5. Limits and failure semantics

P03-04 inherits the P03-03 finite input/event/node/depth/text/attribute/namespace limits. Token, element, stack, ordered-attribute and output buffers use fallible reservation where the standard library permits it. No extra unbounded resolver, DOM, filesystem, network, process or writer capability is introduced.

`PreservingXmlError::code()` delegates P03-03 safety failures to their existing `safe_xml_*` code and adds only:

- `preserving_xml_invalid_span`;
- `preserving_xml_token_mismatch`;
- `preserving_xml_tree_invalid`;
- `preserving_xml_allocation_failed`;
- `preserving_xml_untouched_mismatch`.

Messages never contain untrusted XML text, names, values or paths. No partial token document is returned.

## 6. Compatibility boundary

P03-03 `PackageGraph` continues to consume its existing event model and error mapping. The new ordered safe-attribute metadata and source spans are crate-internal additions and do not change PackageGraph v1 semantics.

This task proves the token model against synthetic XML only. It does not classify whole HWPX parts, apply patches, serialize modified XML, write ZIPs, inspect a user document or run 한글 2020. Those claims remain unverified until their later tasks.
