# P06 table number-format v0 to v1 migration

`hwpx-agent.table-number-format/v1` replaces implicit mutation of the `number_format` field with an
exact, separately versioned operation contract.

Callers must provide a complete logical master-cell snapshot bound to one canonical `TableGrid`.
Each cell supplies stable identity, top-left coordinate, non-formula payload digest, property digest,
and an optional complete `FormulaCell`. Formula owners must equal their master-cell coordinates.

Requests now carry the exact table identity, selected formula master cells, target typed format,
source-state SHA-256 and document-flow SHA-256. Selection order is canonicalized. Empty, duplicate,
covered-slot, non-formula, stale or over-limit input fails closed. The builder repeats every state,
grid and flow check and returns no partial plan.

The migration changes no HWPX grammar. Standard `ResultFormat` tokens and exact Hangul 2020 native
spelling remain evidence inputs for a later separately versioned direct adapter. Existing raw format
strings must not be reinterpreted as this typed operation without explicit validation.
