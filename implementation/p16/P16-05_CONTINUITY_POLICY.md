# P16-05 project continuity policy

## Resource and compatibility

- Resource: `ui://hwpx-agent/project-continuity/v1.html`.
- MIME: `text/html;profile=mcp-app` from the official MCP Apps package.
- Render tool: `render_project_continuity_widget`, read-only and `project.read` only.
- The self-contained HTML is capped at 800,000 bytes. CSP connect and resource domains are empty;
  frame domains are absent. External URLs, resources, forms, frames and storage are forbidden.
- P16-04 `ui://hwpx-agent/document-work/v1.html` and its source-lock contract remain byte-identical.
  Continuity is additive because its HTML/CSS/JavaScript behavior is a separate versioned surface.

## Tool-call policy

| Action | Public tool | Required properties | Admission |
|---|---|---|---|
| Refresh head | `project_open` | exact approved surface/locale/project, fresh request ID, closed include list | read-only |
| Refresh history | `project_history` | exact approved context, fresh request ID, diff summary true, page size 12 | read-only |
| Save checkpoint | `project_checkpoint` | exact current head as expected and target revision, UUID idempotency key, fixed label | second UI click plus host/server authorization |

The view never treats UI state as authorization. A conflict other than `none`, missing head, pending
action, identity mismatch, schema mismatch or tool error prevents the write. There is no automatic
retry and therefore no accidental second write. Server replay results are accepted only through the
same exact public output schema.

## Local E2E

The E2E harness loads the production resource in a real Chrome iframe and connects the real MCP Apps
`AppBridge` over `PostMessageTransport`. It sends approval-gated input and the initial result, then
performs the visible Refresh, Create checkpoint and Confirm and create clicks. It asserts exactly
three calls in `project_open`, `project_history`, `project_checkpoint` order and verifies the write's
project, expected revision, revision, label and idempotency-key presence.

Chrome runs headless in a temporary isolated profile with background networking and DNS resolution
disabled. The harness is local test evidence and is not shipped as the widget resource. Each
published receipt is Git-ignored, atomic, unique and contains no document data, path, credential or
raw browser output.

## Claim boundary

This card may pass only as a local MCP Apps bridge/component E2E. It does not prove actual
ChatGPT/Codex rendering, plugin registration, Developer mode, a remote MCP server, production OAuth,
Hangul/COM execution, file transfer, 2022/2024 or another PC. The roadmap checkbox remains open until
an explicit actual-host session supplies the required Web-to-Codex acceptance evidence.
