# P17-04 integrated main-root plugin binding v2

Date: 2026-09-06
Scope: current PC, installed personal plugin root binding
Decision: **PASS for the current-PC integrated main-root plugin binding**

The v1 local MCP and personal-plugin qualification remains immutable. After its independent audit,
the implementation branch was fast-forwarded into the stable product root `D:\개발\hwpx-agent`.
The personal plugin MCP arguments were rebound from the temporary implementation worktree to that
main root, and both the Node bridge and Rust daemon were rebuilt there.

The plugin creator cachebuster procedure assigned version `0.1.0+codex.20260906011622`. The old
installed cache was removed, the plugin was installed again from the personal marketplace, and
`codex mcp get` confirmed an enabled stdio registration with no environment values. A fresh
ephemeral read-only Codex session called only `local_companion_health` and returned the exact ready
result for the current Hangul 2020 profile with automation and product networking disabled.

Clean main commit `0f408de00620bf4227a124e6a14c5fc6fe04fc08` produced successor run
`890e1150a2184172abbe8af0ef3eb7b2`, which passed all 11 checks through another fresh Codex session.
Its canonical receipt has SHA-256
`61d60800a2a86277ccc215f3f6d2a92f1fb97f2101a841667e39fe7da04b5cbd`. It stores only hashes and
bounded identifiers, not the absolute plugin, product or workspace paths.

No Hangul process, document, COM call, persistent credential, PostgreSQL service or production
distribution is part of this binding update.
