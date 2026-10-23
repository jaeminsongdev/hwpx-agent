# P09 owned oracle diagnostics v0 → v1

This additive failure-only diagnostic projection is not a DB-schema migration, role grant or product acceptance upgrade. Original PostgreSQL migrations and success-path completion semantics stay unchanged.

| v0 | v1 |
| --- | --- |
| Original legacy seven-key diagnostic | Kept unchanged; optional forty-key exact-call-context observation added |
| Completion error | Same primary error; diagnostic failures cannot mask it |
| Broad prefix-based reason extraction | Exact literals allowlisted from original pinned SQL sources |
| Application role | Same privileges; no diagnostic DB reads |
| Missing raw historical failure logs | Still unavailable, no reconstructed cause |

New optional `owned_oracle_observation` is either a fixed unavailable state or schema `hwpx-agent.p84-owned-oracle-observation/v1`. `checks` has exactly forty known keys, values strictly Boolean or null. IDs, raw logs, SQL and exception messages are omitted. Duplicate, missing or extra keys and non-Boolean values are rejected.

The private context is admitted only for ten original owned fixtures. The original runner checks disposable-container ownership, loopback and no host mounts before observation. Its existing admin connection, not the application account, may issue the pinned read-only query. This document does not authorize a run.

State `observed_after_failure_NOT_original_atomic_oracle_or_cause` always has `original_atomic_oracle_verified=false` and `root_cause_proven=false`. Consumers must not treat any combination of observations as original atomic qualification, SQL-cause closure, native acceptance or Gate PASS. Lease timing and concurrent head state can differ after failure.
