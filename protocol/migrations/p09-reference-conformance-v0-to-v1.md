# P09 reference conformance v0 to v1 migration

There was no prior machine-readable P09 conformance matrix.

## Added

- `hwpx-agent.p09-reference-conformance/v1`
- exact REF-001 through REF-053 catalog ordering
- exact P09/P11 ownership reconciliation
- ten typed component profiles with normalized source/test locks
- per-row required validation and fixture inventories
- explicit direct-HWPX, target, render, automation, differential and green states

## Compatibility

Consumers must reject missing, duplicate, reordered or additional rows; component collisions;
P11-to-P09 ownership promotion; altered source locks; unknown fields; and any target/green claim not
backed by a future versioned evidence migration. Absence of evidence is `not_run`, never `pass`.
