# P15-05 artifact delivery policy

Date: 2026-09-05
Scope: current development PC, licensed Hancom Hangul 2020, local reference delivery boundary
Status: implementation candidate until the P15-05 report closes the card

## Public boundary

The P15-02 `artifact_get` input and output schemas remain byte-identical. The P15-03 handler still
authenticates the public user, validates the exact schema, authorizes tenant/project membership,
dispatches once, validates structured output and checks request/resource correlation. P15-04 job
behavior and event metadata remain unchanged.

`metadata` returns only the frozen structured descriptor. `preview` returns
`preview_in_meta`; `attachment` returns `attachment_in_content` and adds one MCP `resource_link` with
an opaque `hwpx-artifact://` URI. The model-visible structured result and resource link never contain
artifact bytes, filesystem paths, encryption data or signed credentials. A short-lived HTTPS URL is
placed only in client-only `_meta["hwpx/artifactDelivery"]` together with its exact expiry, stable
artifact URI, `Accept-Ranges: bytes` capability and response-size limit.

The local reference does not claim that an unintegrated client can resolve the opaque resource URI.
P15-09 and P16 must bind this typed result to the selected MCP SDK/host transport without moving the
signed credential into model-visible content.

## Authorization and signed delivery

- `artifact_get` first passes the shared public OAuth scope and project-membership policy. The
  gateway then requires an exact tenant/project/artifact binding and the P14 artifact service
  rechecks tenant plus subject ACL.
- Project bindings are finite and generation fenced. Revocation increments the generation and
  immediately invalidates URLs issued under the older generation. Re-registration receives another
  generation; an old token cannot revive.
- Preview and attachment require an `available` and `verified` artifact. Metadata may be read only
  through the P14 metadata ACL and does not create a delivery URL.
- The P15 URL is HMAC-SHA256 signed by a distinct reference key and binds version, key ID, operation,
  tenant, project, artifact, authenticated subject digest, content SHA-256, semantic request digest,
  binding generation, issue time and expiry. Exact canonical field order and constant-time signature
  verification are mandatory.
- The public schema permits 30 through 900 seconds. Configuration chooses a default within that
  range and may choose a stricter maximum, but never exceeds 900 seconds. Expiry is returned as an
  exact UTC RFC 3339 timestamp and a token is rejected after that instant.
- The URL owner uses a zeroizing value and every Debug implementation redacts it. Signed URLs,
  bearer tokens, artifact bytes, document content and local paths are not logged or stored in
  structured output.

## Byte-range redemption

Redemption re-verifies the signature, expiry, tenant, subject, current binding generation, P14
artifact ACL/state and plaintext SHA-256 before any bytes are returned. Only one strict `bytes=`
range is accepted:

- closed (`bytes=2-5`), open-ended (`bytes=12-`) and suffix (`bytes=-4`) forms;
- end offsets beyond the object are clamped to the last byte;
- multiple, whitespace-containing, noncanonical, reversed and zero-suffix ranges are rejected;
- an offset at or beyond the object returns typed unsatisfiable state with only the total length;
- full and partial responses are bounded by the configured maximum; a large full response requires
  an explicit bounded range;
- success records 200 or 206 semantics and, for partial output, exact `Content-Range`.

The reference source decrypts and integrity-checks the complete bounded P14 local object before
slicing it. This proves semantics, not production streaming efficiency. P15-09 must provide the
actual HTTPS adapter and a production object store must implement bounded positional/streamed reads.

## Deferred claims

No Hangul process, COM call, HWPX/PDF/user document, system setting or external network service is
needed for this card. Production key custody, CDN/object-store URL signing, HTTP cache headers,
multi-process binding persistence, transport streaming, upload, hosted ChatGPT/Codex attachment
resolution and Hancom 2022/2024 remain unverified.
