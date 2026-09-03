# VS-0 create request v0 to v1

`hwpx-agent.vs0-create-request/v1` is the first executable product-vertical request contract. The
earlier VS-0 design and roadmap entry were non-executable v0 requirements and remain historical input;
no v0 wire payload is accepted or rewritten.

## v1 boundary

- Input is an exact-field JSON object containing the schema version, bounded idempotency/project/
  document/base-revision identities, expected head generation, one page preset, one style preset and
  one bounded text value.
- `expected_head_generation` is exactly `1`, `page_preset` is `a4_portrait`, and `style` is `default`.
- Text is nonempty single-paragraph Unicode, NFC-normalized at the semantic boundary, limited to
  4,096 UTF-8 bytes, and rejects disallowed controls and noncharacters.
- Raw XML, HAction/COM strings, backend identifiers, filesystem destinations and arbitrary package
  options are not representable.
- Output `hwpx-agent.vs0-create-result/v1` exposes only state, replay marker, revision generation,
  artifact/result/plan/route digests and counts. It does not expose document text or private paths.

## Compatibility and failure policy

Unknown or duplicate fields, missing/oversized identities, invalid text, stale head, mismatched key
reuse, unsigned or wrong-target route evidence, invalid package closure, publication conflict and
runtime evidence drift fail closed. There is no best-effort fallback, schema downgrade or partial
result. Unit and E2E negative tests cover unknown fields, wrong shape, key-reuse drift, text controls,
multiline/oversize values, artifact tamper and actual trace/request duplication.

An incompatible request shape, a larger VS-0 feature set, a different idempotency lifetime, a public
route choice, or changed result semantics requires a new version and migration. Durable cross-process
replay is not silently added to this reference CLI; it must preserve the P04 `IdempotencyStore`
contract and is delivered in P14.
