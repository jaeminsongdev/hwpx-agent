# P04-04 OperationPlan compiler report

- Generated: 2026-09-02
- Audited source commit: `d02d2f14e593dae4707fa3365f6057cc24029779`
- State: `pass_current_pc_local_pure_model`
- Reasoning/review mode: `xhigh / selector, unit, default and dependency compile boundary`

`domain-ir`에 typed `OperationPlanDraft`와 immutable `CompiledOperationPlan` 사이의 pure
fail-closed compiler를 구현했다. exact plan/capability schema version, typed identities,
P04-03 exact-one selector, P04-02 unit normalization/receipt, versioned defaults와 deterministic
dependency DAG를 한 번에 검증한다. 한 operation이라도 실패하면 compiled plan을 반환하지 않는다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Pure compiler boundary | `pass` | filesystem/network/process/COM/HAction/runtime execution dependency 0 |
| Typed/versioned admission | `pass` | plan/operation/capability/revision IDs and exact plan/capability schema versions |
| Selector compile | `pass` | exactly one typed selector; mixed/empty invalid, unsupported weak selectors need resolution |
| Snapshot binding | `pass` | plan revision + selector expectation revision + canonical graph digest must match |
| Unit normalization | `pass` | exact rational mm/pt/HWPUNIT/px/ratio/percent/degree through P04-02 receipts |
| Default provenance | `pass` | fallback/locked policies, caller/default source and canonical value SHA-256 |
| Dependency DAG | `pass` | missing/self/duplicate edges rejected; cycle distinct; stable Kahn order |
| Atomic publication | `pass` | `atomic` only; `best_effort` remains needs-resolution; no partial compiled result |
| Finite bounds | `pass` | capability/operation/dependency/argument/default/string/serialized ceilings |
| Deterministic bytes | `pass` | input-order-independent topological operations, sorted dependency arrays and BTree arguments |
| Privacy | `pass` | Debug/errors redact IDs, revisions, selectors, targets and argument values |

## Validation evidence

- Windows Rust 1.96.0: compiler `9/9`; combined `domain-ir` `36/36`, doc tests and Clippy
  `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, source/registry read-only, Cargo offline, executable temp mounts; compiler `9/9`,
  combined `36/36` and Clippy passed.
- Fixed-seed DAG: 1,000 operations with deterministic shuffle and reversed input compile to
  byte-identical canonical JSON; operation count and dependency order remain exact.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact implementation commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Security: exact implementation checkout and clean clone each scanned 532 files;
  secrets/vulnerabilities/forbidden licenses 0; current SBOM 271 and clean-clone SBOM 229
  components.
- P04-01 graph golden and P04-02/P04-03 regressions remain green on Windows/Linux.

## Strict self-review and remediations

- Change risk: `high` because the router/executor will trust compiled targets, units and order.
- An unqualified `best_effort` policy could later permit partial mutation. v1 accepts only atomic;
  best-effort requires an independence contract and returns `needs_resolution`.
- Capability definitions/defaults initially lacked aggregate admission bounds. Definition count,
  arguments per definition and total default bytes now have hard ceilings.
- Argument keys are restricted to bounded ASCII identifiers to prevent visually confusable or
  platform-sensitive parameter names. Text values retain deterministic LF/tab while rejecting
  other control characters.
- Locked defaults compare normalized canonical values, so different source units cannot bypass or
  falsely trigger a conflict after exact conversion.
- Missing/self/duplicate dependency and cycle failures are separated; ready-node ties use typed ID
  order rather than input order.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P04-04 proves typed in-memory compilation against synthetic graphs/capability definitions. It does
not deserialize the public permissive JSON design schema, mutate a document, route/execute a backend,
prove capability availability, or open Hancom. No user document was opened or modified. Public JSON
admission remains a separate deny-unknown adapter Gate; other PCs/releases remain deferred.

## Next exact task

Start `P04-05 Capability router` with reasoning effort `xhigh`. Route compiled operations only when
support evidence, policy, preservation impact and backend health all admit one deterministic route.
Unknown/stale registry state, disabled production/provider scope, preservation loss and unhealthy
backend must fail closed without fallback escalation. P04 final Gate remains `max`. No user local
operation is required for P04-05.
