# Workspace transaction v0 to v1 migration

P04-06 replaces ad-hoc temp-file execution with `hwpx-agent.execution-manifest/v1` and
`hwpx-agent.workspace-transaction-receipt/v1`.

Callers must stop passing source paths as output destinations, backend action strings or independent
operation receipts. They must first construct one manifest from the complete compiled plan and its
exact route set, then provide a source artifact whose size/SHA-256 matches that manifest.

The transaction engine owns job-path hashing, create-new staging, bounded output readback,
validation, same-volume no-overwrite artifact publication and revision CAS ordering. Callers must
handle `rolled_back`, `quarantined`, `revision_cas_committed`, `completed` and `incomplete` as
different outcomes. A CAS conflict after artifact publication is not success and its artifact must
remain orphan-quarantined. A post-CAS interruption is not safe to roll back and must be reconciled.

Unknown states, illegal transitions, source/manifest/route drift, traversal/link sources, oversized
artifacts, validation failure and existing destinations fail closed. Public wire adapters must deny
unknown fields and enforce serialized-size ceilings before constructing the Rust in-memory types.
