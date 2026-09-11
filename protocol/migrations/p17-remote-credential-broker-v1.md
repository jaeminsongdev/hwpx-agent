# P17 remote credential broker v1 migration

This private successor composes the existing credential lifecycle v1, pinned TLS transport and
Windows Credential Manager custody without changing any public P00-P16 protocol.

The earlier lifecycle component stopped before network and storage side effects. The new private
issuer wire uses distinct `HWPXCIQ1`/`HWPXCIP1` framing, a fresh bounded compact-JWS client bearer,
TLS 1.3 with an exact leaf certificate pin, canonical request-digest-bound responses and a separate
explicit rejection outcome. TLS identity, framing, trailing-data, response-digest and JSON failures
remain nondefinitive and therefore do not clear pending state.

The broker state is an append-only canonical JSON log. Each immutable record binds its sequence,
predecessor digest and complete lifecycle-policy digest. A pending record is accepted before network
dispatch. Verified nonsecret metadata is accepted before writing or deleting the exact vault target.
Only an observed vault digest or absence permits the final stable record. Recovery can therefore
finish a vault write/delete whose return path was lost, or replay the exact issuer request when a
prepared access token was not written.

`WindowsCredentialManagerProvider` remains a single-attempt read type. The new
`WindowsCredentialManagerVault` exposes observe/write/delete only through the broker vault trait and
never enumerates credential targets. Existing v1 custody evidence remains valid for the retrieval
type; it is not promoted into broker or issuer evidence.

Compatibility and rollback:

- No stable lifecycle JSON is silently interpreted as a broker record. A new broker log starts only
  when the exact vault target is absent.
- Policy, sequence, predecessor, canonical encoding or vault digest drift fails closed without
  overwriting the current record.
- Broker logs contain no raw token. Rolling back code leaves the Windows credential and append-only
  records untouched for explicit reconciliation.
- Cross-system ACID atomicity and power-loss durability are not claimed. The implemented guarantee
  is ordered no-overwrite publication plus process-crash/ambiguous-result reconciliation.
- The current qualification uses an ephemeral loopback issuer and a unique synthetic Windows
  credential. It is not an external issuer, real service credential, registered host or production
  qualification.
