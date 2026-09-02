# P04-06 Workspace transaction policy

## Scope

`operation-engine` owns the filesystem transaction boundary after P04-04 compilation and P04-05
routing. It does not parse public JSON, lower semantic operations, execute a backend, call Hancom,
COM/HAction, use the network or update a real database. P04-06 accepts synthetic proposed output
bytes so the isolation, publication and revision-CAS protocol can be proved before backend wiring.

## Immutable admission

`ExecutionManifest` is constructed from the complete immutable `CompiledOperationPlan` and exactly
one `RouteDecision` per compiled operation. Construction rejects missing, duplicate or mismatched
operation/capability routes and mixed target-profile or signed-registry snapshots. It binds:

- typed transaction, plan, source-artifact and base-revision identities;
- expected source SHA-256 and size;
- canonical compiled-plan SHA-256;
- deterministic ordered route-set SHA-256 and route count;
- exact target profile and registry payload digest/sequence.

Job-relative paths never contain caller identities. They are derived from SHA-256 of the transaction
ID; artifact names are output content hashes. Traversal-like identity text therefore cannot become a
filesystem component.

## State and source invariants

The only success path is:

```text
received -> planned -> preconditions_verified -> workspace_prepared -> executing
 -> readback -> validating -> artifact_committed -> revision_cas_committed -> completed
```

Skip, repeat, backward and post-terminal transitions fail. Recovery terminals are `rolled_back`,
`quarantined` and `incomplete`.

The source is opened with read-only `File::open`, must be a regular non-link/non-reparse file outside
the workspace, and must match expected size and SHA-256 before staging. A separate pre-execution
observation is compared after success or recovery. A pre-existing mismatch is reported as
`source_identity_mismatch` with unchanged evidence; only observed mid-transaction drift becomes
`source_mutation_detected`. The source path is never passed to a write, move, remove or publication
operation.

## Staging, commit and recovery

Source and proposed output bytes are copied into a per-job `SecureWorkspace` staging directory with
create-new writes and durability sync. Output is reopened, bounded and checked against its staged
size/SHA before a caller-supplied validator can admit it. Publication uses same-volume hard-link
create-new semantics, sync and staging removal. Existing artifact names are never replaced.

Before artifact commit, any error removes only the job staging subtree and becomes `rolled_back`.
After artifact commit but before successful revision CAS, conflict/failure/interruption moves the
complete artifact to create-new orphan quarantine. Quarantine hard-links and syncs the complete file
before removing the public name. If durability/removal/recovery cannot prove one final name, the
receipt is `incomplete`/`committed_outcome_uncertain`; it is never promoted to completed.

Once CAS reports committed, later interruption cannot delete or quarantine the committed artifact.
The receipt remains at `revision_cas_committed` or `completed` so P04-08 reconciliation can act on
the exact outcome.

## Fault and privacy model

Deterministic fault points exist before and after all nine normal steps plus rollback and quarantine.
The committed matrix requires source observation equality and artifact bytes to be absent, complete
in quarantine, or complete in public output—never partial. Limits bound source/output/manifest bytes.
All public errors use stable codes; Debug output omits paths, identities, hashes and document bytes.

Actual backend execution, semantic output validation, persistent revision/CAS storage, idempotency,
garbage collection and crash/process-kill testing are later Gates. Other PCs and Hangul versions are
not involved in this task.
