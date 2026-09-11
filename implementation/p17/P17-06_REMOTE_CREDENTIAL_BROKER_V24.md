# P17-06 credential broker fixed sequence publication slot v24

Date: 2026-09-11

Decision: **broker concurrent-publication defect repaired; component PASS; P17-06 remains open**

The v22 broker stored each immutable record under a final name containing both the sequence and
record digest. Its pre-publication revision check was exact for a single writer, but the filename
left more than one publication path for one sequence. Two processes that both observed the same
predecessor could therefore publish different records for the same sequence. A later scan rejected
the duplicate sequence, but rejecting the already-corrupted directory is not compare-and-append.

The broker now uses exactly one final path, `{sequence:020}.json`, as the no-overwrite publication
slot. The exact record SHA-256 remains derived from the accepted bytes and remains the predecessor
revision binding; it is no longer part of the filename. Each writer creates and syncs a bounded
same-directory temporary file, then attempts a hard link to the fixed slot. Once one link succeeds,
all competing writers for that sequence receive `StoreFailure::Conflict` and remove their own
temporary file.

A synchronized 32-writer test gives every writer a different valid canonical sequence-one record.
Exactly one writer succeeds, 31 conflict, reopening yields one valid record, and the directory has
only `00000000000000000001.json`. Reopen, canonical encoding, sequence, predecessor, policy,
temporary-file bounds and content tamper checks remain fail closed. Complete broker state,
credential lifecycle, pending request metadata, vault reconciliation and token non-persistence are
unchanged.

The v22 evidence and v1 private contract are immutable predecessors. The v24 report, v2 migration,
v2 private contract and v3 evidence record the repair without re-running or upgrading the earlier
synthetic Windows Credential Manager and pinned loopback TLS execution. Those runtime claims are
carried only through the exact v2 evidence digest. The new direct evidence is a locked/offline Rust
test of the file-state component.

No external issuer, external network, real assertion, real service credential, registered host,
power-loss test or production run occurred. P17-06 and product completion remain false.
