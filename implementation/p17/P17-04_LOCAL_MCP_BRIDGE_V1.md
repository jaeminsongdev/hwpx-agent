# P17-04 local stdio MCP bridge v1

Date: 2026-09-06
Scope: current PC, local-only health boundary
Decision: **PASS for current-PC local MCP config and personal plugin fresh-install smoke**

## Bounded increment

`@hwpx-agent/local-companion-mcp` exposes exactly one read-only stdio MCP tool,
`local_companion_health`. The tool has an exact empty input schema: callers cannot provide a path,
token, document value or backend action.

Each admitted call creates a fresh 32-byte random base64url token, starts the qualified Rust daemon
with an absolute binary and configuration path, passes only the token plus bounded Windows runtime
roots in its environment, sends one private authenticated health request, closes stdin and requires
the child to exit cleanly. The token buffer is zeroized in the bridge and the daemon. Output is
bounded, canonical, exact-shape and rejected if it contains a token or configured path.

The public result contains only readiness, the exact current-PC Hangul 2020 profile, disabled
automation/network flags, workspace count and a configuration digest. Errors collapse to one
content-free message. The bridge does not launch Hangul, read a document, connect to a network,
persist a credential or expose a plan-review/PostgreSQL route.

The machine-readable boundary is `protocol/private/p17-local-mcp-v1.json`. The clean-commit
acceptance must prove modern MCP initialization, one-tool discovery, strict schema rejection, the
actual Node-to-Rust call, redaction, shutdown and cleanup before the bridge can be qualified.

Clean repair commit `62844aef98cb114e08ac2e394ef5fbad32565bbb` produced bridge run
`d1a376b7563c4654b15fccbaa98645e0`, which passed all 12 checks. The canonical receipt has SHA-256
`c6ca18e2ad30454850b53284227f23abed10871e1ce532a633b8279550817c3e`.

The personal package `hwpx-agent-local@personal` was then scaffolded with the plugin creator,
validated, discovered in the default personal marketplace and installed. `codex mcp get` reported
the server enabled with stdio transport and no environment values. A fresh ephemeral read-only Codex
session called only `local_companion_health` and returned `ready` for the exact current profile with
automation and network both false.

Clean commit `e942e000be88894c70150af3a266bb892be8fa9e` then produced installed-plugin run
`273f6ccaac644836814b87679ab4eb0c`, which repeated and bound all 12 checks through a new ephemeral
Codex session. Its canonical receipt has SHA-256
`c421cfcefc0157ad2eea1b6d3cb7f8bf0bdb6931b2fe630d2857ede6ce6ec332`. The local plugin manifest,
MCP configuration and runtime configuration are bound by digest; no raw private path is copied into
the checked-in qualification.

The first clean-commit acceptance attempt stopped before MCP startup because the Python harness did
not resolve the Windows `pnpm.cmd` shim while keeping `shell=False`. It produced no PASS evidence.
The second attempt reached the actual health call but the harness expected invalid tool input as a
top-level JSON-RPC error. MCP SDK 2.0 correctly represents `tools/call` validation failures as an
`isError: true` tool result. Neither failed attempt is PASS evidence. The harness now requires that
exact bounded error form, verifies it has no structured output, and still rejects any reflected
private path or fixture content. A fresh clean repair-commit run is required.

## Explicit non-claims

- The plugin is installed only in the current user's personal Codex environment; it is not a
  production or distributable package claim.
- The current pre-install conversation does not gain the new tool retroactively; two new ephemeral
  Codex sessions discovered and called it successfully.
- No persistent credential provider, PostgreSQL lifecycle or plan-review host is connected.
- No Hangul process, access prompt, COM call, user document or network connection is used.
