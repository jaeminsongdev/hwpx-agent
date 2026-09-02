# P04-04 OperationPlan compiler policy

- Effective date: 2026-09-02
- Plan contract: `hwpx-agent.operation-plan/v2`
- Capability definition contract: `hwpx-agent.capability-definition/v1`
- Implementation: `crates/domain-ir/src/operation_plan.rs`

## Compile boundary

`OperationPlanCompiler` consumes a bounded typed `OperationPlanDraft`, a validated immutable
`CapabilityCatalog`, and the P04-03 snapshot/expectation pair. It returns an immutable
`CompiledOperationPlan` only after every operation, selector, argument, default, dependency and
serialized-size check succeeds. There is no partially compiled public result.

The Rust draft is the executable core contract. `specs/operation-plan-v2.schema.json` remains a
design/wire input; a future API adapter must reject unknown/mixed fields and compile them into these
types without exposing raw backend actions.

## Selector admission

A `SelectorDraft` contains exactly one P04-03 typed selector. Empty or mixed variants are invalid.
Bare text offsets, cursor/session and page-position inputs return `operation_plan_needs_resolution`;
they are not weakened into another selector. Plan `base_revision`, selector expectation revision and
snapshot graph digest must all remain current before target resolution. Each operation receives one
exact resolved target or the complete compile fails.

## Arguments, units and defaults

Capability definitions are versioned and identified by typed `CapabilityId`. Argument keys are
bounded ASCII identifiers. Supported kinds are text, boolean, bounded integer, length, typography,
ratio and angle. Numeric drafts use exact `RationalInput` and must include a compatible `NumericUnit`:

| Canonical kind | Admitted source units |
|---|---|
| length micrometers | mm, pt, integer HWPUNIT, px with explicit DPI |
| point-milli | pt |
| ratio-millionths | ratio, percent |
| angle-microdegrees | degree |

P04-02 performs checked normalization and emits the stored `ConversionReceipt`. Missing units return
`needs_resolution`; incompatible units and non-integer HWPUNIT fail as invalid arguments; DPI and
arithmetic failures remain typed unit-conversion errors. Every compiled value has a SHA-256 digest.

Defaults exist only inside a versioned capability definition. `fallback` applies only when the
caller omitted the argument. `locked` accepts a caller value only when its normalized canonical value
equals the locked default; disagreement returns `needs_resolution`. `ArgumentSource` records caller
or capability-default provenance. Unknown arguments and missing required values fail closed.

## Dependency and publication rules

Operation IDs are unique typed IDs. Missing, self and duplicate edges are invalid. Kahn ordering uses
ordered sets/maps, so every ready-node tie is resolved by stable operation ID, not input order.
Cycles return `operation_plan_cycle`. Dependency arrays are sorted in the compiled artifact.

`atomic` is the only admitted v1 compile policy. `best_effort` remains `needs_resolution` until a
later capability/executor contract proves operation independence. Compiled JSON is compact,
deterministic and carries exact schema, plan/revision/graph identity, resolved targets, normalized
arguments/receipts and topological operations. Debug and error output redact all identities, values,
selectors and targets.

## Finite limits and scope

Default limits are 10,000 operations, 100,000 dependencies, 1,024 arguments per operation, 256 KiB
per string, 16 MiB aggregate argument bytes and 64 MiB compiled JSON. Capability definitions,
arguments and defaults also have hard count/byte ceilings.

This compiler does not mutate a graph, route a backend, execute a capability, open Hancom, implement
transactions or deserialize untrusted public JSON. Those boundaries remain P04-05/P04-06 and later
API phases.
