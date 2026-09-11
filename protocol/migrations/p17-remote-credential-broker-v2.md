# P17 remote credential broker v2 migration

This private successor repairs the append-only broker log's final-name namespace. The v1 format
used `{sequence:020}-{record_sha256}.json`; v2 uses the single fixed
`{sequence:020}.json` publication slot while continuing to derive the revision SHA-256 from the
exact canonical record bytes.

Compatibility and admission:

- A v2 store does not reinterpret or rename an existing v1 directory. A directory containing v1
  digest-bearing names is rejected as unknown input.
- Operators must quiesce the old broker and explicitly reconcile or export its latest validated
  nonsecret state before starting a new v2 directory. This component does not provide or claim an
  automatic state migration.
- New v2 stores start only through the existing broker open rule: both the dedicated log and exact
  vault target must be absent. Existing credentials are never enumerated or deleted.
- The fixed final path is the compare-and-append slot. Same-directory temporary files remain
  bounded, synced and individually removed after either successful publication or conflict.
- Rollback leaves all v2 record files and vault contents untouched for explicit reconciliation.
  A v1 binary fails closed on the v2 filename rather than silently adopting it.

The wire, lifecycle, canonical record payload, policy binding, predecessor digest, vault ordering
and recovery rules do not change. Cross-system atomicity, directory-fsync/power-loss durability,
hostile administrator resistance, external issuer operation and production readiness remain
unclaimed.
