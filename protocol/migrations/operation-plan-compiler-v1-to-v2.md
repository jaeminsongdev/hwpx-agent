# OperationPlan compiler v1 to v2 migration

`hwpx-agent.operation-plan/v2` is the first executable typed compiler contract. Earlier v1 examples
and the permissive design JSON schema are not accepted as proof of a compiled plan.

## Required changes

- use typed plan, operation, capability and revision IDs;
- pin the exact graph digest through a P04-03 selector expectation;
- provide exactly one admitted typed selector per operation;
- replace numeric JSON values with exact rational value plus explicit compatible unit;
- source defaults only from a versioned capability definition and retain default provenance;
- reject unknown arguments, missing required arguments and locked-default conflicts;
- reject missing/self/duplicate dependencies and cycles;
- publish only deterministic topologically ordered atomic compiled plans.

`best_effort`, cursor/session, bare offset and page-position drafts require a later explicit contract
and remain `needs_resolution`. Public JSON deserialization/generation must be added behind its own
deny-unknown schema Gate; clients must not treat Rust enum serialization as the final public API.
