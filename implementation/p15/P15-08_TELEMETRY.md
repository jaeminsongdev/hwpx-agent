# P15-08 bounded telemetry and dashboard design

Date: 2026-09-05
Scope: current development PC, licensed Hancom Hangul 2020, local MCP control-plane reference
Status: implementation candidate until the P15-08 report closes the card

## Boundary and lifecycle

Every MCP call creates exactly one internal observation before tool admission and commits exactly one
complete trace after the public result has been constructed. Telemetry wraps the existing boundary;
it does not reorder authentication, strict JSON parsing, schema validation, authorization, quota
admission, the single gateway dispatch, output validation or result correlation. The bounded local
collector has no I/O or fallible export path after construction, so it cannot replace an already
executed product result with an observability error.

The digest-pinned `protocol/mcp/p15-telemetry-policy-v1.json` fixes a 2,048-trace maximum and the
six-stage hierarchy:

`mcp_request → capability_plan → job → backend_execution → validation_step → artifact_commit`

All six spans exist in every retained trace. A span is `completed`, `failed` or `not_applicable`;
absence of a job or artifact is never reported as completed work. When the ring is full, the oldest
whole trace is removed before the new complete trace is appended. No partial trace is retained.

## Correlation and privacy

The internal chain uses `request_id`, `job_id`, a per-dispatch internal `execution_id`, `revision_id`
and artifact evidence. Each value is converted to a process-salted SHA-256 digest before storage.
The random salt stays in memory, is redacted from `Debug`, is never serialized and changes at process
restart. Capability IDs receive the same treatment. Raw tenant IDs, subjects, project/request/job/
revision IDs, filenames, paths, document content, arguments, bearer tokens, signed URLs, arbitrary
backend strings and backend errors have no field in the trace schema.

Only closed enums and bounded numeric aggregates are retained. Tenant classification is limited to
`unattributed` before authentication and `local_reference` after authentication; this supplies the
current-PC tenant-class SLI dimension without recording an identity or inventing a production tier.
Backend routing accepts only the frozen public enum values plus the internal
`control_plane` class. Renderer provenance remains in the validated product result and arbitrary
renderer strings are not copied into telemetry.

The public MCP response adds only `hwpx/telemetryPolicySha256`. Internal trace IDs and dashboard data
are not added to `structuredContent`, `content` or `_meta`.

## Dashboard snapshot

`InMemoryTelemetry::dashboard` derives a deterministic snapshot from retained complete traces rather
than maintaining a second unbounded index. It includes:

- tool count and latency totals/maxima by tool, caller class and success/error;
- closed job lifecycle-state count by success/error;
- backend route count by closed backend class and success/error;
- salted capability-route count by selected backend and success/error;
- validation-state count by success/error;
- retained capacity and whole-trace eviction count.

This qualifies the P15-08 `tool/job/backend/capability` local SLI and sample-trace requirement. It does
not claim hosted dashboards, percentile accuracy, long-term retention, cross-process correlation,
distributed exporters or production SLO compliance.

## Failure interpretation

Admission/authentication/parse/input failures mark `mcp_request` failed and later spans not
applicable. A policy failure marks `capability_plan` failed. A gateway failure marks
`backend_execution` failed. An invalid or miscorrelated gateway result records completed backend
execution followed by failed validation, while the invalid payload itself is discarded. Artifact
commit is completed only when a schema-valid result explicitly reports `commit_state=committed`.

## Deferred claims

No Hangul process, COM call, HWPX/PDF/user document, network collector or external account is used by
this card. Windows worker process signals, package/parser metrics, real renderer timings, production
OpenTelemetry export, alerting, incident automation and hosted retention remain later integration and
release-Gate work. Hancom 2022/2024 remain deferred to their own PCs.
