# P03-07 Preserving patch engine policy

- State: implemented for current-PC local core and approved disposable 한글 2020 validation
- Contract: `hwpx-agent.preserving-patch/v1`
- ID profile: `hancom-2020-hwpml-2011-core/v1`
- Product boundary: pure in-memory typed patch transaction; no filesystem or ZIP publication
- Consumer: P03-08 atomic preserving/normalized package writers

## 1. Admission and immutable source

`PreservingPatchEngine` accepts an already bounded reader and supplied `PackageGraph`, then rebuilds P03-05 preservation evidence and P03-06 `IdIndex`. Any graph drift, rejected part, unsafe XML or invalid reference blocks planning. Only `TokenStable` XML parts admit XML selectors. Source ZIP and part bytes are never modified.

The transaction loads verified part bytes into private memory, applies a complete plan to private copies, builds a validation-only in-memory ZIP, and reruns `BoundedZipReader`, `PackageGraph`, `PreservationReport` and `IdIndex`. No result is returned unless every layer succeeds. This validation archive is not a P03-08 publication writer: it has no filesystem target, overwrite, crash-commit or external byte-return capability.

## 2. Public capability and non-disclosure

The v1 intent allowlist is exactly:

- `ReplaceAttribute`
- `ReplaceText`
- `InsertSibling`
- `DeleteSubtree`
- `ReplaceSubtree`
- `AllocateId`
- `AddRelationship`
- `AddPart`

Public intents do not accept unchecked byte offsets. `XmlElementSelector`, `XmlAttributeSelector` and `XmlTextSelector` can only be bound from a validated immutable `PreservingXmlDocument`; they capture source SHA-256, token/tree index, namespace-resolved expected name and token kind. Apply rechecks all captured facts against preservation evidence.

`PatchText`, `ValidatedXmlFragment`, `AddedPart` and `RelationshipAddition` retain semantic values or bytes privately. Their `Debug` implementations expose only structural metadata, bounded lengths and approved hashes; no text, attribute value, relationship ID, fragment bytes, part bytes or filesystem path is printed. `PatchResult` publishes part path, disposition, length and hashes but retains the actual output artifact privately for P03-08. `verify_artifact_integrity` recomputes only path/size/hash correspondence.

## 3. XML mutation rules

- Text and attribute replacements accept XML 1.0 characters only and encode `&`, `<`, `>` plus the active attribute quote. Callers cannot inject markup through a semantic value.
- A fragment must parse through P03-03/P03-04 as exactly one root element spanning the whole input. BOM, XML declaration, DTD, custom entity, PI, CDATA, surrounding bytes, malformed namespaces and multi-root content are rejected.
- Namespace declarations cannot be replaced as ordinary attributes. Inserted/replacement fragments carry their own valid namespace bindings.
- Root deletion and root sibling insertion are rejected. Root replacement remains possible only with one validated full element.
- Every edited XML part is reparsed before package validation. Untouched ranges are copied directly from the immutable source; untouched parts retain exact SHA-256 equality.

## 4. Conflict and deterministic ordering

The engine resolves all selectors and normalizes every mutation to a checked half-open source range before applying anything. It rejects:

- overlapping non-empty ranges;
- an insertion inside or on either boundary of a replacement/deletion range;
- multiple insertions at one anchor;
- ancestor deletion/replacement overlapping a descendant patch;
- multiple allocations or edits that target the same attribute span.

It does not infer an execution order for these cases. Non-conflicting edits are ordered by canonical part key and source span and applied once against the original offsets. Add-part and allocation requests are normalized independently of caller intent order.

## 5. Typed ID allocation

`AllocateId` requires a P03-06 profiled decimal declaration attribute and an expected `IdKind`. Existing declarations are never renumbered. Requests are sorted by `(part namespace, IdKind, AllocationHandle)` and reserve a contiguous block beginning at the checked maximum existing value plus one. A `ReplaceAttribute` may refer to an opaque `AllocationHandle` without receiving the numeric value.

Duplicate/missing handles, text-ID fields, kind mismatch and range exhaustion fail. Because the engine is a pure transaction and publishes no global allocator state, any failure discards all reservations. Post-patch `IdIndex` must again have zero duplicate, dangling, wrong-type, malformed or unknown-ID issues.

## 6. Relationship and part addition

`AddRelationship` produces one internal OPF manifest item and optionally one typed spine item. Relationship IDs use the P03-06 safe text-ID grammar; targets are validated non-directory portable package paths; media types use the P03-02 parser. External, traversal, ambiguous and missing targets fail through admission or rebuilt graph validation.

`AddPart` accepts either a fully parsed safe XML document or non-XML opaque bytes. XML-looking bytes under non-XML media and known binary signature mismatch are rejected. An added part must have exactly one relationship in the same transaction with the same target and media type. Existing/casefold/NFC path collision, orphan, duplicate manifest target and overwrite all fail closed. P03-08 will decide final compression/publication; v1 uses private validation-only compression.

## 7. Limits and failure behavior

`PatchLimits` validates nonzero hard-ceiling values for intent count, changed-plus-added part count, semantic value bytes, fragment bytes, added part bytes and total positive output growth. Added part content counts toward total growth. Size arithmetic is checked and owned allocations use fallible reservation where controlled by this module.

Errors expose stable non-sensitive codes. There is no partial `PatchResult`, partial graph, partial `IdIndex`, filesystem artifact, allocator reservation or mutable source state on failure.

## 8. Validation scope

The committed corpus covers all eight intents, XML escaping, untouched hashes, duplicate/overlap/nesting/boundary conflicts, stale selectors, root mutation, malicious fragments, deterministic allocation, failed-transaction retry, relationship/part atomicity, order independence, finite limits and 64 fixed-seed random sequences. The whole `hwpx-package` regression corpus remains mandatory.

The `validate_patch_engine` example reads only explicitly supplied approved fixture paths. It performs a no-op artifact integrity pass and a private in-memory `itemref@linear` typed mutation, then prints only fixture ordinal, profile and aggregate counts. It never writes a file or starts 한글/COM/UI.

This v1 policy does not claim schema-level semantic validity for every unknown HWPML element, public output bytes, ZIP publication, crash/no-partial filesystem commit, normalized writer behavior, user-document completeness, actual 한글 reopen/save/render, or 2022/2024 compatibility.
