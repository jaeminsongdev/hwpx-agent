# P17-06 pinned issuer transport and Windows credential broker v22

Date: 2026-09-11

Decision: **current-PC broker component PASS; P17-06 remains open**

`remote-credential-wire` now separates issuer traffic from the remote-sync protocol with bounded
framing and zeroizing credential-bearing response buffers. `PinnedCredentialIssuerTlsTransport`
uses TLS 1.3 only, an exact DNS identity and leaf-certificate pin, no ambient trust roots, one
provider-supplied bounded compact-JWS client bearer per exchange, canonical response JSON and exact
request-digest binding. Only an explicit
request-bound rejection received through that authenticated channel is definitive. Connection,
certificate, frame, trailing-byte, digest and JSON failures retain pending state.

`remote-credential-broker` composes all four lifecycle operations with a vault and state store. Its
append-only record phases are stable, awaiting issuer, prepared access and prepared revocation.
Every record binds the exact policy, sequence and predecessor digest. A synced temporary file is
published under a digest-bearing sequence name using a no-overwrite hard link. Pending is published
before dispatch; verified metadata is published before vault mutation; the vault digest or absence
is observed before the final stable record.

This is a recovery protocol, not a false cross-system transaction claim. If a vault write succeeds
but its return or stable append fails, the prepared metadata and observed digest finish the commit
without another issuer request. If the write did not occur, the exact request is replayed and the
same verified metadata is required. Revocation similarly recovers from deletion before the result
or stable append. An unexpected vault digest, orphaned credential, noncanonical record, broken
sequence, policy drift, expired pending request or generation mismatch fails closed.

`WindowsCredentialManagerVault` implements exact-target observe/write/delete without enumeration;
observe returns only absence or SHA-256. The existing provider stays read-only and single-attempt.
Secret values are bounded to 2,560 bytes, zeroized in process buffers and absent from state JSON,
errors, evidence and `Debug`.

Focused locked/offline validation passed: lifecycle 15/15, broker 13/13, issuer wire 2/2, TLS 10/10
(including four issuer cases), and Windows custody unit tests 3/3. An explicit ignored current-PC
qualification also passed end-to-end with one unique synthetic Credential Manager target:
`pending -> pinned loopback TLS 1.3 issue -> signed access verification -> actual vault write/read ->
stable -> signed revocation -> actual delete -> terminal state`. Seven immutable state records were
observed and the owned credential was absent after cleanup. Pure failpoint tests cover ambiguous
write/delete results and stable-append failures; refresh and rotate pass in the same model but were
not exercised against Windows Credential Manager in the side-effect qualification.

Evidence is at
`implementation/p17/evidence/credential-broker/p17-remote-credential-broker.current-20260911.v2.json`.
It SHA-binds and preserves the earlier v1 qualification rather than replacing it.
The private contract, migration, validator and tamper tests bind the exact sources, limits, recovery
ordering and nonclaims.

The issuer is ephemeral and loopback-only. Client-assertion signature/freshness, Windows power-loss
durability, an independently operated external issuer, real client assertion, real service
credential, external network, registered host,
production, P17-06 completion and product completion remain unverified and false.
