# P15-03 MCP handler policy

Date: 2026-09-04
Scope: current development PC, licensed Hancom Hangul 2020, in-process reference handlers
Status: implementation candidate until the P15-03 report closes the card

## Fixed boundary

Every public call follows one fail-closed sequence:

1. admit only an exact P15-02 tool name and a bounded raw argument payload;
2. authenticate a public-user bearer against the descriptor's exact OAuth scopes;
3. parse JSON while rejecting duplicate keys at every nesting level;
4. validate the complete input against the embedded P15-02 Draft 2020-12 schema;
5. authorize tenant, project, subject and project access without causing a document effect;
6. dispatch exactly one authorized call to a service gateway;
7. validate the returned structured value against the matching output schema;
8. verify request and common resource correlation, then return a bounded MCP result.

Authentication precedes JSON parsing. Gross tool-name and byte-size checks are transport admission
guards and may reject before authentication. Every authentication failure at a known tool returns the
descriptor's OAuth discovery challenge without parsing or reflecting arguments.

## Trust boundaries

- `McpControlPlane` owns the local reference `AuthMiddleware`, compiled schema catalog, policy and
  service gateway. A gateway never receives a call unless authentication, schema and policy pass.
- `AuthorizedToolCall` carries the typed tool, authenticated tenant and subject, request/project
  correlation and a canonical argument digest. Its debug form redacts identities and arguments.
- `InMemoryProjectPolicy` is a finite local reference adapter. Cross-tenant and non-member projects
  are indistinguishable from missing. State-creating tools require editor/owner project membership;
  `artifact_get` and the five P15-02 read-only tools may use reader membership.
- The service gateway remains responsible for repository-level ownership of every nested revision,
  artifact, job, plan and checkpoint identifier. The generic boundary does not trust IDs merely
  because their syntax is valid.
- The gateway is invoked at most once. Handlers never run COM, HWPX ZIP mutation, subprocesses or
  network I/O directly.
- Gateway errors are reduced to stable categories. Raw backend errors, schema diagnostics, tokens,
  paths and document content are not returned.

## Input and output safety

The raw argument ceiling is 262,144 bytes and JSON recursion remains bounded by the parser. The
P15-02 schemas impose tighter per-field limits. Authorization headers and raw argument buffers use
zeroizing owners; parsed values are never logged or included in debug output.

The pinned `jsonschema 0.53.0` dependency is compiled without default features. Its transitive
`borrow-or-share 0.2.4` dependency is licensed under OSI-approved `MIT-0`; both the Rust license
allowlist and the repository-wide dependency policy explicitly admit `MIT-0`, and those policy files
are part of this card's source lock.

Successful results include the schema-valid `structuredContent`, one fixed concise text item and
client-only catalog/request metadata. Error results use the preliminary
`hwpx-agent.tool-error/v1` envelope and set `isError=true`. P15-06 will freeze the complete public
error catalog; P15-03 intentionally exposes only stable safe categories needed by this boundary.

The output `request_id` must equal the validated input. When both input and output name a
`project_id`, `job_id`, `revision_id` or `release_label`, those values must also match. An invalid or
mis-correlated backend value is discarded and replaced with a safe error.

## Scope and later work

This card implements reusable in-process Rust handlers and contract tests. It does not implement
Streamable HTTP, an MCP SDK adapter, a production identity provider, PostgreSQL/object-store wiring,
long-running progress, cancellation execution, artifact byte delivery, quotas, telemetry, MCP
Inspector or ChatGPT/Codex connection. Those remain P15-04 through P15-09 work.

No Hancom process is needed for this boundary. The only selectable runtime profile remains the exact
current-PC P15-02 value `hancom-hangul-2020-secondary`; 2022/2024 remain deferred.
