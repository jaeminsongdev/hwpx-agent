# P17-06 Windows credential custody v18

Date: 2026-09-11

Decision: **current-PC Windows Credential Manager custody mechanism PASS; P17-06 remains open**

The independent `windows-credential-custody` crate now provides a Windows-only
`WindowsCredentialManagerProvider` over `local-sync`'s unchanged credential-provider trait. It
reads one compact JWT body from a deterministic generic-credential target and reconstructs the
existing bounded `AuthorizationHeader` only in zeroizing memory. The provider has no product write,
update, search or delete API, redacts its locator in `Debug`, and consumes its single retrieval
attempt even when the credential is missing or the store is unavailable.

Service and account locators are nonempty opaque ASCII identifiers bounded to 120 bytes and may
contain only alphanumerics, dot, underscore and hyphen. The resulting colon-delimited target is
unambiguous. Secret input is bounded to 2,560 bytes, the exact Win32 generic credential blob
ceiling. Empty, oversized, non-UTF-8, malformed-JWT, ambiguous and malformed-store inputs fail
closed; malformed bytes carried by a dependency error are zeroized before discard.

The explicit current-PC qualification created one UUID-derived synthetic generic credential with
`Local` persistence only after an exact `NoEntry` preflight. The product provider read it once,
accepted the authorization shape, refused a second retrieval, left the stored value present after
read, redacted secret and locator debug output, deleted the exact owned entry, and proved exact
`NoEntry` afterward. The locked/offline test passed 1/1. Routine workspace runs keep this
side-effecting qualification ignored. All existing `local-sync` all-target tests remain unchanged;
the new crate's two pure tests pass by default and its one native qualification is ignored except
when explicitly requested.

Evidence is recorded at
`implementation/p17/evidence/credential-custody/p17-windows-credential-custody.current-20260911.v1.json`.
It retains only the generated target SHA-256 and booleans—no raw target, JWT, authorization header,
credential value, existing-entry listing, path or user document. Contract
`hwpx-agent.windows-credential-custody-contract/v1` and its validator reject evidence, dependency,
limit, failure-policy and nonclaim drift.

This closes only the current-PC secure persistent-store retrieval mechanism. A trusted real
credential installer, issuer/refresh and rotation lifecycle, revocation, real service credential,
remote TLS transport, registered-host integration, production authentication and disaster recovery
were not exercised. Actual remote network, production, P17-06 completion and product completion
remain false. The next MAX increment is a certificate-pinned remote TLS transport plus an external
issuer/rotation lifecycle that consumes this provider without exposing credentials.
