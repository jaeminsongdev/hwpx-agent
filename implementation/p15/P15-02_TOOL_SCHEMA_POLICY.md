# P15-02 Public MCP tool schema policy

Date: 2026-09-04  
Scope: current development PC, licensed Hancom Hangul 2020, contract-only  
Status: implementation candidate until the P15-02 report closes the card

## Outcome

P15-02 freezes exactly 18 public, user-intent-level MCP tools. The checked-in catalog contains a
self-contained JSON Schema Draft 2020-12 input schema, a concise structured-output schema, OAuth
scope declarations, and safety annotations for every tool. It exposes neither the internal COM
surface nor raw HWPX XML, filesystem paths, credentials, or document bytes.

This card does not implement the MCP transport, handlers, authorization server, hosted OAuth,
ChatGPT widget, or any Hancom 2022/2024 behavior. Those claims remain open. The next P15 cards must
consume this catalog without silently widening it.

## Authoritative sources

The contract follows the official OpenAI MCP server, plugin reference, and tool-definition guidance
retrieved on 2026-09-04:

- https://developers.openai.com/plugins/build/mcp-server
- https://developers.openai.com/plugins/reference
- https://developers.openai.com/plugins/plan/tools

Accordingly, each descriptor has an action-oriented name and title, an explicit usage description,
an input schema, an output schema for `structuredContent`, truthful annotations, a top-level
`securitySchemes` declaration, and an identical `_meta.securitySchemes` compatibility mirror.
Descriptions state limits and distinguish adjacent tools.

## Exact public surface

The order is normative and deterministic:

1. `capability_check`
2. `document_plan`
3. `document_create`
4. `document_inspect`
5. `document_edit`
6. `document_transform`
7. `template_analyze`
8. `document_validate`
9. `document_render`
10. `document_export`
11. `project_create`
12. `project_open`
13. `project_history`
14. `project_checkpoint`
15. `project_publish`
16. `job_get`
17. `job_cancel`
18. `artifact_get`

Internal capability IDs such as `page.paper_preset` remain data inside these tools. They never become
one public MCP tool per capability.

## Schema constraints

- Every object rejects unknown properties, including nested request and result objects.
- Every array and free string is bounded. Identifiers use typed prefixes and bounded ASCII patterns.
- The target profile is the exact current-PC identifier `hancom-hangul-2020-secondary`. It does not
  imply Hancom 2022/2024 compatibility.
- Mutation inputs carry an exact `expected_revision` and UUID `idempotency_key`; the first project
  creation explicitly uses a null expected revision.
- A tool that may create only job, evidence, snapshot, contract, preview, or delivery-grant state
  still carries an `idempotency_key`, even when it does not create a document revision.
- Export creates a separate local artifact and loss report. It cannot upload, email, print, or
  otherwise transmit content.
- Structured results contain bounded metadata and artifact references only. Artifact bytes,
  attachment bodies, signed delivery URLs, secrets, access tokens, local paths, and large widget
  payloads belong in MCP `content` or client-only `_meta`, outside these output schemas.
- Actual missing validation backends remain `unverified`; schemas contain no route that promotes
  `not_run` or `unverified` to `pass`.

## Safety annotation decisions

`readOnlyHint=true` is used only when every valid call is unable to create a job, revision, artifact,
durable snapshot, receipt, or signed delivery grant. This yields five read-only tools:
`capability_check`, `document_plan`, `project_open`, `project_history`, and `job_get`.

Several tools are semantically read-only with respect to document bytes but conservatively use
`readOnlyHint=false` because a valid call may create durable service state:

- `document_inspect` may materialize a snapshot artifact.
- `template_analyze` may materialize a template contract.
- `document_validate` creates a job and evidence.
- `document_render` creates a job and preview artifact.
- `artifact_get` may create a short-lived delivery grant.

`destructiveHint=true` applies only to `job_cancel`, because cancellation may irreversibly prevent
that job from completing. Document edit/transform/export and project checkpoint/publish are false:
they use immutable revisions or labels and do not overwrite the source. All 18 tools are replay-safe
or observationally idempotent, so `idempotentHint=true`. All 18 use `openWorldHint=false`: no tool in
this surface sends mail, uploads publicly, prints, signs through an external provider, or modifies an
external service. These hints do not replace server-side authorization, precondition validation,
confirmation, or policy enforcement.

## Authentication and tenant boundary

Every descriptor is OAuth2-only and declares the least P15-01 scopes needed for its broadest valid
behavior. The top-level and `_meta` declarations must be byte-equivalent as JSON values. The catalog
uses only the eight scope strings frozen by `p15-auth-tenant-v1.json`; it cannot introduce an
unregistered permission. Handler-level authorization and tenant/resource ownership checks remain
mandatory in P15-03 and later.

## Generated artifacts and drift detection

`tools/p15/build_public_tool_schemas.py --write` deterministically creates:

- `protocol/mcp/p15-public-tools-v1.json`
- `implementation/p15/p15-public-tool-schema-snapshot-v1.json`
- `implementation/p15/p15-public-tool-schema-contract-v1.json`

The snapshot records the canonical SHA-256 of the full catalog and every descriptor/input/output
schema. The contract digest-locks the generator, catalog, snapshot, policy, validators, tests,
P15-01 scope contract, and docs-lane wiring. `--check` and
`tools/p15/validate_public_tool_schemas.py` fail closed on generated drift, unknown tools, schema
weakening, annotation drift, auth mirror drift, source drift, or invalid representative instances.

## Later gates

P15-03 must bind handlers to these exact descriptors and revalidate all inputs and structured
outputs server-side. P15-09 must use MCP Inspector against the real Streamable HTTP server. Only a
later PC with the licensed target installed may create separate Hancom 2022/2024 evidence; this card
does not predeclare those profiles.
