# P17 remote TLS transport v1 migration

This additive private contract introduces an independent `remote-tls-transport` crate implementing
the existing `local_sync::RemoteTransport` interface. Existing loopback TCP, credential-provider,
host and wire implementations remain unchanged. No caller is automatically migrated.

Construction requires one exact numeric `SocketAddr`, one canonical lowercase DNS identity, one
bounded DER certificate and a 1 ms through 60 s timeout. Product configuration must choose
`PublicRemote`, which accepts only conservatively classified public unicast addresses. The separate
`LoopbackQualification` scope accepts loopback addresses only and can never establish production
or external-network evidence. IP-literal TLS identities and implicit DNS resolution are rejected.

The supplied DER certificate is the only rustls trust anchor. The client enables TLS 1.3 only with
the explicit ring provider and retains normal WebPKI signature, validity and DNS-name checks. After
that handshake it also requires the peer leaf DER SHA-256 to equal the supplied certificate before
writing authorization or request bytes. No custom certificate verifier or ambient root store is
used.

The transport reuses the bounded `remote-sync-wire/v1` request and response frames. TLS and
certificate failures are definitive rejection; ordinary connection and I/O failures are
unavailable outcomes. Unknown status, malformed or oversized frames and trailing plaintext fail
closed. A valid authenticated response remains definitive even if local socket teardown later
occurs.

Rollback removes only this independent crate, its workspace membership and the pinned rustls and
rcgen dependency declarations. It does not alter credentials, certificates, endpoint settings,
remote hosts, user documents, prior evidence or existing transports.

The v1 qualification uses ephemeral loopback listeners and per-test synthetic certificates. It
proves a local TLS 1.3 transport component, not an external remote network, real service
certificate, real service credential, issuance or rotation, registered-host integration,
production authentication, P17-06 completion or product completion.
