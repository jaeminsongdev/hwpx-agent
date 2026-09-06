# P17-08 trusted local Git approval widget v7

Date: 2026-09-06
Scope: current-PC React MCP App, local stdio bridge and personal plugin
Decision: **trusted widget boundary implemented; P17-08 remains in progress**

The v0.4 local companion replaces the model-visible raw-token execution tool from v0.3 with a
`react-widget` confirmation surface. The read-only
`local_companion_prepare_git_commit_approval` tool renders the self-contained
`ui://hwpx-agent/local-git-approval/v1.html` resource. The widget displays the bounded workspace,
output pathspec, commit message, current HEAD, branch and output/plan digests. It requires an explicit
acknowledgement checkbox before its single destructive button is enabled.

The destructive `local_companion_confirm_and_execute_git_commit` tool is declared with
`_meta.ui.visibility=["app"]`. It accepts only the displayed plan bindings and a 256-bit component
challenge. The challenge is returned in tool-result `_meta`, never in model-visible structured
content, is capped to 128 pending entries, expires after 300 seconds and is consumed before any
asynchronous work. The server then reads the current Git plan again. Any changed HEAD, branch,
output digest, target digest or plan digest rejects the request without executing Git.

Only after the second plan matches does the bridge generate a 32-byte process-local key, mint a
60-second exact-request confirmation internally and pass it to the bounded Rust effect child. The
key is not stored in the plugin manifest, MCP configuration, runtime configuration or filesystem.
The model and widget cannot supply an actor, tenant, signing key or confirmation token. JavaScript
strings cannot be guaranteed zeroized, so the base64url child-environment copy is treated as
short-lived process memory rather than claimed secure erasure.

Commits `c1358b3`, `43c391c` and `1c7d1ea` implement the widget, bound resource response and
process-local authority. The widget package passed 133 tests and the MCP package passed 13 tests.
Clean source commit `1c7d1ea` produced actual disposable acceptance run
`2eddeec06b824857af3c546f7e32e328` under `artifacts/p17/mcp-approval-effect-runs/`. All 20 checks
passed through MCP stdio, the Node bridge, the Rust daemon and the current PC Git executable. The
run verified the seven-tool catalog, app-only metadata, closed-CSP resource, component-only
challenge, internal confirmation, exact commit bytes and parent, unrelated staged-entry
preservation, second-use rejection, cleanup and absence of Hangul/network/user-repository use.

Personal plugin `hwpx-agent-local@personal` was updated to
`0.4.0+codex.20260906130036` with no MCP environment variables or persisted secret. A fresh Codex
session successfully called `local_companion_health`, and another fresh Codex session successfully
prepared the exact plan for a copied synthetic HWPX in the dedicated disposable workspace. Those
diagnostics prove the installed plugin can start v0.4 and reach the prepare boundary, but they are
not a trusted confirmation click.

The canonical installed-plugin successor run `9e2a6c6e958642e6a7f72dc9dac0bf25` passed all 18
checks from clean source commit `48061260f36619077fb8114ecb8eb86c18edbca5`. It bound the exact
installed arguments and hashes for Node, the bridge, daemon, widget, Git executable and three plugin
configuration files. One fresh session called health exactly once and a second called only the
read-only prepare tool. The disposable repository HEAD, index, status and output hash were identical
before and after; no approval-state file remained. The checked-in qualification intentionally records
`actual_trusted_ui=false`, `actual_git_effect=false` and `actual_hangul=false`.

P17-08 therefore remains open. The remaining acceptance is a visible MCP App render in a freshly
loaded Codex task, an actual user checkbox/button action, receipt verification in the disposable
workspace and replay rejection. No Hangul process or access prompt is part of this Git-widget gate.
