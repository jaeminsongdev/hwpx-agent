# P17-06 remote TLS transport v19

Date: 2026-09-11

Decision: **current-PC loopback TLS 1.3 component PASS; P17-06 remains open**

The independent `remote-tls-transport` crate now implements `local_sync::RemoteTransport` for one
exact numeric endpoint and one exact DNS identity. The constructor performs no DNS lookup and
requires an explicit endpoint scope: `PublicRemote` conservatively rejects loopback, private,
link-local, documentation, benchmark, multicast and reserved address ranges, while
`LoopbackQualification` accepts loopback only. An IP literal cannot be used as the TLS server name.

The transport configures rustls 0.23.43 with the ring provider and TLS 1.3 only. It starts from an
empty root store, adds only the supplied bounded DER certificate, and uses the normal WebPKI path,
signature, validity and DNS-name verification. After the handshake it independently compares the
peer leaf DER SHA-256 with the supplied certificate digest. Authorization and request bytes are not
written until both layers pass. There is no custom permissive verifier and no ambient system or
bundled root fallback.

The existing bounded `remote-sync-wire/v1` format carries the request and response. Invalid
certificates, wrong names, wrong pins, invalid scopes, malformed or oversized frames, unexpected
trailing plaintext and unknown status fail closed. Ordinary endpoint or I/O unavailability remains
distinct from definitive TLS, certificate, configuration or protocol rejection. `Debug` redacts
the endpoint, identity, leaf digest and rustls configuration.

Six locked/offline Rust tests passed on this PC. They cover an exact-pin/name TLS 1.3 exchange;
wrong-pin and wrong-name refusal before request dispatch; all remote statuses; trailing-byte and
unavailable-endpoint typing; configuration, timeout, certificate and debug bounds; public versus
loopback endpoint admission including IPv4 and IPv6; IP-identity rejection; and malformed
certificate/frame behavior. The qualification creates only ephemeral loopback listeners and
per-test synthetic certificates and leaves no persistent credential, certificate or listener.

Contract `hwpx-agent.remote-tls-transport-contract/v1`, its migration note, validator and tamper
tests bind the dependency versions, trust model, address scope, wire policy, source invariants and
nonclaims. Evidence is recorded at
`implementation/p17/evidence/remote-tls/p17-remote-tls-transport.current-20260911.v1.json`.

No external endpoint, real service certificate, real service credential, certificate lifecycle,
credential issuance or rotation, registered host, production network or disaster recovery was
exercised. Actual external remote network, production, P17-06 completion and product completion
remain false. The next MAX increment is an external issuer/refresh/rotation lifecycle and then one
independently controlled certificate-pinned remote service qualification.
