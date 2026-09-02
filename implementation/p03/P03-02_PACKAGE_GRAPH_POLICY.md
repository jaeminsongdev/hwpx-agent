# P03-02 PackageGraph policy

- State: implemented for synthetic current-PC local core validation
- Product boundary: read-only HWPX package metadata and part closure
- Upstream boundary: `P03-01` bounded classic ZIP reader
- Standard source: locked KS X 6101 machine-readable source, package sections 8.3/8.4

## 1. Public contract

`hwpx-package` publishes `PackageGraph`, `PartRecord`, `Relationship`, `MediaType`, `PartRole`, `RelationshipKind`, validated `PackageGraphLimits` and stable `GraphError::code()` values. Graph construction accepts only a previously opened `BoundedZipReader`; it reuses that reader's validated `PackageLimits` and cannot substitute a looser path policy.

The graph contains no raw XML. A part record contains its portable package path, declared or infrastructure media type, graph role, expanded size and SHA-256 of the fully integrity-read raw part. A relationship contains a typed source, target, media type, kind and spine linearity.

## 2. Required HWPX infrastructure

The following checks occur before graph publication:

1. entry zero is the exact root name `mimetype`;
2. it uses ZIP `Stored` compression and its bytes are exactly `application/hwp+zip` with no BOM or whitespace;
3. `version.xml` and `META-INF/container.xml` exist as files;
4. container XML declares the OCF namespace `urn:oasis:names:tc:opendocument:xmlns:container` and exactly one `rootfile` with `full-path` and a valid `media-type`;
5. the rootfile exists and declares an OPF `package` in either the exact standard URI `http://www.idpf.org/2007/opf` or the exact trailing-slash URI `http://www.idpf.org/2007/opf/` emitted by the current 한글 2020 fixture; arbitrary trimming or other near-match URI is rejected;
6. exactly one OPF `manifest` and one OPF `spine` are accepted.

Duplicate archive names and NFC/casefold path collisions are already rejected by P03-01. A directory entry is never a part node. Current 한글 2020 may declare multiple container rootfiles: exactly one package root media type is selected, all ancillary rootfile targets must exist, and declared media types are preserved. The fixed preview image `Preview/PrvImage.png` is an allowlisted HWPX infrastructure part with `image/png`; arbitrary unlisted files remain orphan failures.

## 3. Relationship and closure policy

- Manifest items require non-empty unique `id`, `href` and a syntactically valid media type.
- `href` is strict UTF-8 after percent decoding. Both package-root and OPF-source-relative candidates are checked against existing entries; exactly one existing candidate is selected, the same normalized candidate is deduplicated, and two distinct existing candidates fail as ambiguous.
- `.` is normalized, `..` is permitted only while it remains inside package root, and absolute, empty-component, backslash, query, fragment, drive/stream and invalid portable names are rejected.
- A URI scheme or network-path reference is an external relationship and is blocked by default.
- Different relationship spellings that normalize to the same portable collision key are duplicates.
- Every manifest target must be an existing non-directory part.
- Every spine `idref` must resolve to one manifest item. Duplicate spine targets are rejected regardless of `linear=yes|no`.
- Every non-directory archive entry must be either manifest-listed or an allowlisted package infrastructure part. Otherwise graph construction fails with `orphan_part`.

The infrastructure allowlist is the package document plus `mimetype`, `version.xml`, `META-INF/container.xml` and the standard optional OCF metadata names `manifest.xml`, `metadata.xml`, `signatures.xml`, `encryption.xml`, and `rights.xml` under `META-INF`. Allowlisting a name does not parse, trust, execute or expose its contents.

## 4. Narrow XML safety boundary

P03-02 does not publish a general XML parser. It uses `quick-xml = 0.42.0` with all reader checks enabled only for container and OPF graph metadata.

- metadata part: default 2 MiB, hard 16 MiB;
- XML events: default 100,000, hard 1,000,000;
- depth: default 64, hard 256;
- attributes per element: default 32, hard 256;
- aggregate attribute bytes per element: default 8 KiB, hard 64 KiB;
- simultaneously active namespace bindings: derived from attribute/depth limits and capped at 4,096;
- manifest plus spine relationships: default/hard 16,384;
- media type: default 255 bytes, hard 1,024 bytes.

All configured values are finite, non-zero and rejected above their hard ceiling. DTD, named general entities other than XML's five predefined references, processing instructions and CDATA are rejected. Numeric references are accepted only for valid XML Unicode scalar ranges. Only UTF-8 XML declarations are accepted. The parser has no filesystem or network resolver. Unknown OPF metadata subtrees may be structurally skipped within the same byte/event/depth/attribute bounds; package, manifest, spine, item and itemref elements are position-checked against their namespace-resolved URI, including descendant prefix rebinding.

P03-03 will extract this into a reusable safe XML layer. It may not weaken these limits or enable DTD/entity/network behavior without a versioned migration and negative corpus.

## 5. Publication and compatibility

Graph construction is read-only. Every non-directory part is streamed through P03-01 integrity, expanded-size, CRC and nested-archive checks before hashing. A graph is returned only after relationship closure and orphan checks succeed; no partial graph or raw XML is published.

P03-01's current nested document/archive rejection remains in force. Supporting an intentionally embedded HWPX subdocument requires a later versioned policy and corpus; P03-02 does not silently bypass it.

This policy is synthetic-core evidence only. It does not claim compatibility with an actual user document, a full HWPX corpus, writer preservation, or a Hangul 2020 round trip.
