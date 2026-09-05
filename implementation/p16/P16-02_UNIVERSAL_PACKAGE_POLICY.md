# P16-02 Universal Package Policy

## Decision

The tracked `plugins/hwpx-agent` directory is a minimal, immutable and registration-free universal
package base. It is a valid plugin package source, but it is not represented as a connected or
release-ready product until an actual registered app ID is supplied by a user-confirmed Developer
mode registration receipt.

P16-02 local implementation may validate and deterministically archive this unregistered base. A
registered archive must be built as a new artifact and must not rewrite the tracked manifest or
assets. The absence of registration evidence is an explicit `unverified` state, not a placeholder
string or an empty mapping.

## Package boundary

- The required entry point is `plugins/hwpx-agent/.codex-plugin/plugin.json`.
- Every referenced path starts with `./`, resolves below the package root and names a regular file.
- The P16-02 base contains exactly the manifest, README, 128x128 icon and 512x512 logo.
- The base omits `apps`, `mcpServers` and `skills` until their corresponding evidence/components are
  composed by a later no-overwrite build.
- Public legal/website URLs, screenshots and final publisher identity are omitted rather than filled
  with `example.com`, `YOUR_ORG`, `TBD` or other fake values.
- Text and JSON are bounded UTF-8; PNG dimensions, file sizes and digests are validated.

## Registered app admission

A registered build requires one strict receipt with all of the following:

- schema `hwpx-agent.p16-registration-receipt/v1` and a UUID evidence ID;
- `evidence_kind: actual_developer_mode_registration` and `user_confirmed: true`;
- one bounded registered app technical ID with placeholder/test markers rejected;
- one credential-free exact HTTPS MCP endpoint ending in `/mcp`;
- the exact P16-01 official source-lock digest;
- a UTC timestamp and no unknown fields, tokens, cookies, secrets or authorization values.

The receipt and produced package belong under the already Git-ignored `artifacts/p16/` tree. A test
fixture can exercise pure composition in a disposable temporary directory, but it never qualifies
actual registration or a release artifact.

## Composition and preservation

- Archive entries are sorted, use a fixed timestamp and permissions, and are stored without
  platform-dependent metadata.
- Publication is atomic and no-overwrite. Output may not be placed inside the source package.
- Registration adds only `apps: "./.app.json"` plus the strict `.app.json` mapping in the new
  archive. It does not add a local MCP server or endpoint credentials.
- P16-03 skills and P16-04+ UI resources are separate versioned inputs to later composition. They do
  not mutate this P16-02 base.

## Claim boundary

Passing base validation proves only a bounded, deterministic unregistered package source. Until an
actual receipt exists, `registered_app_mapping`, `connected_plugin`, `Developer mode E2E`, public
hosting, submission, web-to-Hangul execution, Hangul 2022/2024 and another PC remain `unverified`.
