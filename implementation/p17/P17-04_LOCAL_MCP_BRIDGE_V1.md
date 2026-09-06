# P17-04 local stdio MCP bridge v1

Date: 2026-09-06
Scope: current PC, local-only health boundary
Decision: **implementation pending actual clean-commit acceptance**

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

## Explicit non-claims

- No personal Codex marketplace or plugin is installed by this increment.
- No current Codex thread has discovered or called the tool.
- No persistent credential provider, PostgreSQL lifecycle or plan-review host is connected.
- No Hangul process, access prompt, COM call, user document or network connection is used.
