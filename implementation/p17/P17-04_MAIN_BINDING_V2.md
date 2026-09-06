# P17-04 integrated main-root plugin binding v2

Date: 2026-09-06
Scope: current PC, installed personal plugin root binding
Decision: **implementation complete; durable successor receipt pending**

The v1 local MCP and personal-plugin qualification remains immutable. After its independent audit,
the implementation branch was fast-forwarded into the stable product root `D:\개발\hwpx-agent`.
The personal plugin MCP arguments were rebound from the temporary implementation worktree to that
main root, and both the Node bridge and Rust daemon were rebuilt there.

The plugin creator cachebuster procedure assigned version `0.1.0+codex.20260906011622`. The old
installed cache was removed, the plugin was installed again from the personal marketplace, and
`codex mcp get` confirmed an enabled stdio registration with no environment values. A fresh
ephemeral read-only Codex session called only `local_companion_health` and returned the exact ready
result for the current Hangul 2020 profile with automation and product networking disabled.

`run_main_bound_plugin_checks.py` must repeat that observation on a clean main commit and write a
canonical successor receipt. It stores only hashes and bounded identifiers, not the absolute
plugin, product or workspace paths.

No Hangul process, document, COM call, persistent credential, PostgreSQL service or production
distribution is part of this binding update.
