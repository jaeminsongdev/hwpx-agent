# P16-03 Skills Package Policy

## Decision

P16-03 packages exactly nine bounded workflow skills as an immutable component. Every tool name is
resolved from the digest-locked P15 public catalog; a skill cannot name a private method, COM/HAction
identifier or tool that is absent from that catalog.

The component is composed with the P16-02 base only in memory or into a new no-overwrite artifact.
It never changes the tracked base manifest. Composition adds only `skills: "./skills/"` and the nine
skill files. Registration and UI resources remain separate inputs.

## Tool and action boundary

- The canonical catalog is `protocol/mcp/p15-public-tools-v1.json` with exactly 18 tools.
- Each skill has an exact ordered primary tool sequence. The generated contract snapshots every
  referenced tool's required input fields, OAuth scopes and annotations.
- `document_edit` is always described with both required fields `dry_run` and `best_effort`.
- `job_cancel` is the only destructive public tool. It is optional in the resume skill and requires
  a fresh explicit cancellation request and host confirmation.
- There is no public print tool. The validate/export skill may validate, render and export; a direct
  printer request is unsupported and must not be represented as completed.
- Write tools use expected revisions and idempotency keys where required. Source revisions and input
  artifacts are immutable; changes produce a new revision or artifact.

## Routing evaluation boundary

The routing cases contain two positive and two negative prompts for every skill. A deterministic
local evaluator proves the checked-in routing vocabulary and negative exclusions. It is component
evidence only, not proof of ChatGPT host routing. Actual indirect/follow-up/boundary prompts remain
for the user-operated P16-09 Developer mode E2E.

## Claim boundary

Passing P16-03 proves a valid nine-skill package synchronized to the current P15 catalog and a
deterministic local trigger/negative evaluation. It does not prove plugin registration, Developer
mode connectivity, hosted MCP execution, UI behavior, direct printing, Hangul/COM execution,
production readiness, another PC or Hangul 2022/2024.
